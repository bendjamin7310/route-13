// Compile and run the generated MuleSetup.lua against a mocked Roblox model.
//   npm install luau-web
//   node tools/mule/luau_test/run.mjs assets/vehicles/mule
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const here = path.dirname(fileURLToPath(import.meta.url));
const assetDir = process.argv[2] || path.join(here, '..', '..', '..', 'assets', 'vehicles', 'mule');
const modPath = process.env.LUAU_WEB || 'luau-web';
const { LuauState } = await import(modPath);

const manifest = JSON.parse(fs.readFileSync(path.join(assetDir, 'mule_manifest.json'), 'utf8'));
const lua = (s) => JSON.stringify(s);
const rows = manifest.parts.map((p) =>
  `{ name = ${lua(p.name)}, group = ${lua(p.group)}, size = { ${p.size_studs.join(', ')} }, pos = { ${p.centre_studs.join(', ')} } },`);
const moduleSrc = fs.readFileSync(path.join(assetDir, 'roblox', 'MuleSetup.lua'), 'utf8');
const source = [
  fs.readFileSync(path.join(here, 'mock.lua'), 'utf8'),
  'PARTS = {', ...rows, '}',
  'MuleSetup = (function()', moduleSrc, 'end)()',
  fs.readFileSync(path.join(here, 'test.lua'), 'utf8'),
].join('\n');

const state = await LuauState.createAsync();
const compiled = state.loadstring(moduleSrc, 'MuleSetup', false);
if (typeof compiled === 'string') {
  console.error('MuleSetup.lua does not compile:', compiled);
  process.exit(1);
}
const fn = state.loadstring(source, 'test', false);
if (typeof fn === 'string') {
  console.error('harness does not compile:', fn);
  process.exit(1);
}
try {
  await fn();
} catch (e) {
  console.error('FAILED:', e.message || e);
  process.exit(1);
}
