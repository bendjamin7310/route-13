//! rbxconv: JSON-lines instance list -> Roblox binary place (.rbxl) or model (.rbxm).
//!
//! Every line: {"r": id, "p": parent id | null, "c": "ClassName", "props": {...},
//!              "attrs": {...}, "tags": [...]}
//! Property values are plain JSON; their Roblox type comes from the reflection database
//! (so enums are given by item name, colours as 0-1 floats, CFrames as 12 numbers ...).
//!
//! usage: rbxconv place|model|placexml|modelxml <in.jsonl> <out.rbxl|rbxm|rbxlx|rbxmx>
//!        rbxconv inspect <file.rbxl|rbxm>
//!        rbxconv dbdump <out.json>      (reflection database used for typing)

use std::collections::HashMap;
use std::fs::File;
use std::io::{BufRead, BufReader, BufWriter, Write};

use anyhow::{anyhow, bail, Context, Result};
use rbx_dom_weak::{InstanceBuilder, WeakDom};
use rbx_reflection::{DataType, PropertyKind, ReflectionDatabase};
use rbx_types::{
    Attributes, CFrame, Color3, Color3uint8, Enum, Font, FontStyle, FontWeight, Matrix3,
    NumberRange, Tags, UDim, UDim2, Variant, VariantType, Vector2, Vector3,
};
use serde_json::Value;

fn f(v: &Value) -> Result<f32> {
    v.as_f64().map(|x| x as f32).ok_or_else(|| anyhow!("expected number, got {v}"))
}

fn arr<'a>(v: &'a Value, n: usize) -> Result<&'a Vec<Value>> {
    let a = v.as_array().ok_or_else(|| anyhow!("expected array, got {v}"))?;
    if a.len() != n {
        bail!("expected {n} numbers, got {}", a.len());
    }
    Ok(a)
}

fn cframe(v: &Value) -> Result<CFrame> {
    let a = arr(v, 12)?;
    let n: Vec<f32> = a.iter().map(f).collect::<Result<_>>()?;
    Ok(CFrame::new(
        Vector3::new(n[0], n[1], n[2]),
        Matrix3::new(
            Vector3::new(n[3], n[4], n[5]),
            Vector3::new(n[6], n[7], n[8]),
            Vector3::new(n[9], n[10], n[11]),
        ),
    ))
}

/// Find the canonical descriptor for `prop` on `class` (walking superclasses, following
/// aliases).  Returns (canonical name, data type).
fn describe<'a>(
    db: &'a ReflectionDatabase<'a>,
    class: &str,
    prop: &str,
) -> Result<(String, DataType<'a>)> {
    let mut cur = db.classes.get(class).ok_or_else(|| anyhow!("unknown class {class}"))?;
    loop {
        if let Some(p) = cur.properties.get(prop) {
            if let PropertyKind::Alias { alias_for } = &p.kind {
                return describe(db, class, alias_for);
            }
            return Ok((p.name.to_string(), p.data_type.clone()));
        }
        match cur.superclass {
            Some(s) => cur = db.classes.get(s).ok_or_else(|| anyhow!("unknown class {s}"))?,
            None => bail!("{class} has no property {prop}"),
        }
    }
}

fn to_variant(db: &ReflectionDatabase, ty: &DataType, v: &Value) -> Result<Variant> {
    Ok(match ty {
        DataType::Enum(name) => {
            let e = db.enums.get(name).ok_or_else(|| anyhow!("unknown enum {name}"))?;
            let item = v.as_str().ok_or_else(|| anyhow!("enum {name} needs a name, got {v}"))?;
            let n = e.items.get(item).ok_or_else(|| anyhow!("{name} has no item {item}"))?;
            Variant::Enum(Enum::from_u32(*n))
        }
        DataType::Value(vt) => match vt {
            VariantType::String => Variant::String(v.as_str().ok_or_else(|| anyhow!("string"))?.into()),
            VariantType::Bool => Variant::Bool(v.as_bool().ok_or_else(|| anyhow!("bool"))?),
            VariantType::Float32 => Variant::Float32(f(v)?),
            VariantType::Float64 => Variant::Float64(v.as_f64().ok_or_else(|| anyhow!("f64"))?),
            VariantType::Int32 => Variant::Int32(v.as_i64().ok_or_else(|| anyhow!("int"))? as i32),
            VariantType::Int64 => Variant::Int64(v.as_i64().ok_or_else(|| anyhow!("int"))?),
            VariantType::Vector3 => {
                let a = arr(v, 3)?;
                Variant::Vector3(Vector3::new(f(&a[0])?, f(&a[1])?, f(&a[2])?))
            }
            VariantType::Vector2 => {
                let a = arr(v, 2)?;
                Variant::Vector2(Vector2::new(f(&a[0])?, f(&a[1])?))
            }
            VariantType::CFrame => Variant::CFrame(cframe(v)?),
            VariantType::OptionalCFrame => Variant::OptionalCFrame(Some(cframe(v)?)),
            VariantType::Color3 => {
                let a = arr(v, 3)?;
                Variant::Color3(Color3::new(f(&a[0])?, f(&a[1])?, f(&a[2])?))
            }
            VariantType::Color3uint8 => {
                let a = arr(v, 3)?;
                let c = |x: &Value| -> Result<u8> { Ok((f(x)? * 255.0).round().clamp(0.0, 255.0) as u8) };
                Variant::Color3uint8(Color3uint8::new(c(&a[0])?, c(&a[1])?, c(&a[2])?))
            }
            VariantType::UDim2 => {
                let a = arr(v, 4)?;
                Variant::UDim2(UDim2::new(
                    UDim::new(f(&a[0])?, a[1].as_i64().unwrap_or(0) as i32),
                    UDim::new(f(&a[2])?, a[3].as_i64().unwrap_or(0) as i32),
                ))
            }
            VariantType::NumberRange => {
                let a = arr(v, 2)?;
                Variant::NumberRange(NumberRange::new(f(&a[0])?, f(&a[1])?))
            }
            VariantType::Font => {
                let family = v["family"].as_str().ok_or_else(|| anyhow!("font family"))?;
                let weight = match v["weight"].as_str().unwrap_or("Regular") {
                    "Thin" => FontWeight::Thin,
                    "ExtraLight" => FontWeight::ExtraLight,
                    "Light" => FontWeight::Light,
                    "Medium" => FontWeight::Medium,
                    "SemiBold" => FontWeight::SemiBold,
                    "Bold" => FontWeight::Bold,
                    "ExtraBold" => FontWeight::ExtraBold,
                    "Heavy" => FontWeight::Heavy,
                    _ => FontWeight::Regular,
                };
                Variant::Font(Font::new(family, weight, FontStyle::Normal))
            }
            other => bail!("unsupported property type {other:?}"),
        },
        _ => bail!("unsupported data type"),
    })
}

fn attr_variant(v: &Value) -> Result<Variant> {
    Ok(match v {
        Value::Bool(b) => Variant::Bool(*b),
        Value::Number(n) => Variant::Float64(n.as_f64().unwrap()),
        Value::String(s) => Variant::String(s.clone()),
        Value::Object(o) if o.contains_key("cf") => Variant::CFrame(cframe(&o["cf"])?),
        Value::Object(o) if o.contains_key("v3") => {
            let a = arr(&o["v3"], 3)?;
            Variant::Vector3(Vector3::new(f(&a[0])?, f(&a[1])?, f(&a[2])?))
        }
        _ => bail!("unsupported attribute value {v}"),
    })
}

fn build(mode: &str, input: &str, output: &str) -> Result<()> {
    let db = rbx_reflection_database::get()?;
    let mut dom = WeakDom::new(InstanceBuilder::new("DataModel"));
    let root = dom.root_ref();
    let mut refs: HashMap<i64, rbx_dom_weak::types::Ref> = HashMap::new();
    let mut top = Vec::new();
    let mut cache: HashMap<(String, String), (String, DataType)> = HashMap::new();
    let mut counts: HashMap<String, usize> = HashMap::new();
    let mut pending: Vec<(rbx_dom_weak::types::Ref, String, i64)> = Vec::new();
    let reader = BufReader::new(File::open(input).with_context(|| format!("open {input}"))?);
    for (lineno, line) in reader.lines().enumerate() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let rec: Value = serde_json::from_str(&line).with_context(|| format!("line {}", lineno + 1))?;
        let class = rec["c"].as_str().ok_or_else(|| anyhow!("line {}: no class", lineno + 1))?;
        if !db.classes.contains_key(class) {
            bail!("line {}: unknown class {class}", lineno + 1);
        }
        let mut b = InstanceBuilder::new(class);
        let mut refs_here: Vec<(String, i64)> = Vec::new();
        if let Some(props) = rec["props"].as_object() {
            for (k, v) in props {
                if k == "Name" {
                    b = b.with_name(v.as_str().unwrap_or("Instance"));
                    continue;
                }
                let key = (class.to_string(), k.clone());
                if !cache.contains_key(&key) {
                    let d = describe(db, class, k).with_context(|| format!("line {}", lineno + 1))?;
                    cache.insert(key.clone(), d);
                }
                let (canon, ty) = &cache[&key];
                if matches!(ty, DataType::Value(VariantType::Ref)) {
                    // {"ref": id}: resolved once every instance exists
                    let target = v["ref"].as_i64().ok_or_else(|| anyhow!("line {}: {k} needs {{\"ref\": id}}", lineno + 1))?;
                    refs_here.push((canon.clone(), target));
                    continue;
                }
                let var = to_variant(db, ty, v)
                    .with_context(|| format!("line {}: {class}.{k} = {v}", lineno + 1))?;
                b = b.with_property(canon.as_str(), var);
            }
        }
        if let Some(attrs) = rec["attrs"].as_object() {
            let mut a = Attributes::new();
            for (k, v) in attrs {
                a.insert(k.clone(), attr_variant(v).with_context(|| format!("line {}", lineno + 1))?);
            }
            b = b.with_property("Attributes", Variant::Attributes(a));
        }
        if let Some(tags) = rec["tags"].as_array() {
            let mut t = Tags::new();
            for s in tags {
                t.push(s.as_str().unwrap_or_default());
            }
            b = b.with_property("Tags", Variant::Tags(t));
        }
        let parent = match rec["p"].as_i64() {
            Some(p) => *refs.get(&p).ok_or_else(|| anyhow!("line {}: parent {p} not yet defined", lineno + 1))?,
            None => root,
        };
        let r = dom.insert(parent, b);
        if parent == root {
            top.push(r);
        }
        let id = rec["r"].as_i64().ok_or_else(|| anyhow!("line {}: no id", lineno + 1))?;
        refs.insert(id, r);
        for (name, target) in refs_here {
            pending.push((r, name, target));
        }
        *counts.entry(class.to_string()).or_default() += 1;
    }
    for (inst, name, target) in pending {
        let t = *refs.get(&target).ok_or_else(|| anyhow!("ref target {target} not found"))?;
        dom.get_by_ref_mut(inst)
            .unwrap()
            .properties
            .insert(name.as_str().into(), Variant::Ref(t));
    }
    let mut out = BufWriter::new(File::create(output)?);
    match mode {
        "place" | "model" => rbx_binary::to_writer(&mut out, &dom, &top)?,
        "placexml" | "modelxml" => rbx_xml::to_writer_default(&mut out, &dom, &top)?,
        _ => bail!("mode must be place, model, placexml or modelxml"),
    }
    out.flush()?;
    out.into_inner().map_err(|e| anyhow!("flush {output}: {e}"))?.sync_all()?;
    let mut c: Vec<_> = counts.into_iter().collect();
    c.sort_by(|a, b| b.1.cmp(&a.1));
    let total: usize = c.iter().map(|x| x.1).sum();
    println!("wrote {output}: {total} instances");
    for (k, v) in c.iter().take(20) {
        println!("  {k:24} {v}");
    }
    Ok(())
}

fn inspect(path: &str) -> Result<()> {
    let dom = rbx_binary::from_reader(BufReader::new(File::open(path)?))?;
    let mut counts: HashMap<String, usize> = HashMap::new();
    let mut props: HashMap<String, usize> = HashMap::new();
    let mut stack = vec![dom.root_ref()];
    let mut n = 0usize;
    while let Some(r) = stack.pop() {
        let inst = dom.get_by_ref(r).unwrap();
        *counts.entry(inst.class.to_string()).or_default() += 1;
        for (k, v) in &inst.properties {
            *props.entry(format!("{}.{} : {:?}", inst.class, k, v.ty())).or_default() += 1;
        }
        n += 1;
        stack.extend(inst.children().iter().copied());
    }
    println!("{path}: {n} instances (incl. root)");
    let mut c: Vec<_> = counts.into_iter().collect();
    c.sort_by(|a, b| b.1.cmp(&a.1));
    for (k, v) in &c {
        println!("  class {k:24} {v}");
    }
    let mut p: Vec<_> = props.into_iter().collect();
    p.sort();
    for (k, v) in &p {
        println!("  prop {k} x{v}");
    }
    Ok(())
}

/// Dump the bundled reflection database (classes, properties, enums) as JSON.
fn dbdump(path: &str) -> Result<()> {
    let db = rbx_reflection_database::get()?;
    let mut classes = serde_json::Map::new();
    for (name, c) in &db.classes {
        let mut props = serde_json::Map::new();
        for (pn, p) in &c.properties {
            let ty = match &p.data_type {
                DataType::Value(v) => format!("{v:?}"),
                DataType::Enum(e) => format!("Enum:{e}"),
                _ => "?".into(),
            };
            props.insert(pn.to_string(), serde_json::json!({"type": ty, "kind": format!("{:?}", p.kind)}));
        }
        classes.insert(name.to_string(), serde_json::json!({
            "superclass": c.superclass, "properties": props,
            "tags": c.tags.iter().map(|t| format!("{t:?}")).collect::<Vec<_>>()}));
    }
    let mut enums = serde_json::Map::new();
    for (name, e) in &db.enums {
        enums.insert(name.to_string(), serde_json::json!(e.items));
    }
    let out = serde_json::json!({"version": db.version, "classes": classes, "enums": enums});
    std::fs::write(path, serde_json::to_string_pretty(&out)?)?;
    println!("wrote {path}");
    Ok(())
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("inspect") => inspect(&args[2]),
        Some("dbdump") => dbdump(&args[2]),
        Some(mode) if args.len() == 4 => build(mode, &args[2], &args[3]),
        _ => bail!("usage: rbxconv place|model <in.jsonl> <out>  |  rbxconv inspect <file>"),
    }
}
