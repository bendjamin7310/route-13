# Route 13 — Game Design Document

**Version 0.1 · Season 1: "The Sit-Down"**

> *"Nobody on Route 13 sees your face. They see your plate."*

| | |
|---|---|
| **Genre** | Chill road-trip roguelite with a crime story |
| **Platform** | Roblox (PC, mobile, console) |
| **Players** | 1–4 per car, solo or as a co-op crew |
| **One run** | One night · 100 miles · about 35–45 minutes |
| **Inspired by** | *Road 96* (story, characters, choices) × *a dusty trip* (your car, the road, scavenging) |

## Contents

1. [The Pitch](#1-the-pitch)
2. [The Gimmick: The Plate Game](#2-the-gimmick-the-plate-game)
3. [The Run: 100 Miles, One Night](#3-the-run-100-miles-one-night)
4. [The Car](#4-the-car)
5. [The Factions](#5-the-factions)
6. [The Story](#6-the-story)
7. [The Chill Layer](#7-the-chill-layer)
8. [Replayability and Progression](#8-replayability-and-progression)
9. [Building It in Roblox](#9-building-it-in-roblox)
10. [Build Order (MVP Roadmap)](#10-build-order-mvp-roadmap)
- [Appendix A: Starter Plates](#appendix-a-starter-plates)
- [Appendix B: Cast and Places](#appendix-b-cast-and-places)

---

## 1. The Pitch

It's one night on **Route 13**, a hundred miles of desert highway split between the Mafia, the Yakuza, the Triad and a crooked federal task force. You have a car, a full tank, and a glovebox full of other people's license plates.

Everyone on the road reads your plate to decide who you are. Wear the right one and they wave you through. Wear the wrong one and the night gets loud.

Get to the sea at Mile 100 by sunrise.

**What makes it different:** in *a dusty trip*, the zombies don't care who you are. On Route 13, everybody does, and you decide who you are one plate at a time.

### Pillars

1. **Be anyone.** Identity is your main tool. Almost every problem on the road can be solved by being the right person at the right mile.
2. **Chill first, loud when you choose.** A perfect run needs zero fights. Fights happen when you wear the wrong face, or when you want one.
3. **Every run is a story.** Small handcrafted scenes, remixed by the plate you wear, the Runner you play and who you pick up.
4. **The road remembers.** Plates, wrecks, characters and a weekly turf war carry your choices from one run to the next.

### The loop

```
Drive → Read the road → Pick your plate → Get through the mile
  ↑                                                  ↓
Next run ← "What if I wear it THERE?" ← Find a plate with a story
```

---

## 2. The Gimmick: The Plate Game

Every kid on a road trip has played the license plate game. On Route 13, it's how you stay alive.

### 2.1 The whole rule

1. Your car wears **one license plate**.
2. **Everybody reads it** (gangsters, cops, bikers, gas station clerks) and treats you like whoever it belongs to.
3. You can **swap it** whenever you're stopped, **as long as nobody sees you do it.**

That's the entire mechanic: one slot, one action, no menus. Everything else in this document grows out of those three lines.

### 2.2 Why this is the one

- **Simple.** Anyone gets it in one sentence: *"Wear a Mafia plate and the Mafia think you're Mafia."*
- **Every stretch of road becomes a small puzzle, with no new controls.** *"Mafia roadblock at Mile 31, Fed checkpoint at 36, and I'm wearing a Yakuza plate. Where do I swap?"*
- **It multiplies your content.** Every event checks your plate, so one roadblock is five different scenes (see 2.10). Build 20 events, ship 100. For a small team, this is the biggest reason to pick this gimmick.
- **It IS the story.** Every plate belonged to somebody. Put it on and you inherit their friends, their enemies and their unfinished business.
- **It's a perfect Roblox collectible.** Small, readable, rare, tradable, and it looks great on a wall.
- **Brains beat aim.** Chill players ghost through. Action players go loud. Both work.
- **It pays off at the end.** The plate you wear into Mile 100 decides who's waiting at the pier (see 6.6). Your last swap is the last choice of the game.

### 2.3 Cover: Clean → Warm → Burned

Every plate has a **Cover** state, shown on the plate itself in the corner of the screen. No extra bars.

| State | Looks like | What it means |
|---|---|---|
| **Clean** | Shiny | They believe you. |
| **Warm** | Scuffed, orange edge; NPCs get a "?" | They're looking closer: more checks, more favors asked, more searches. Goes back to Clean after 3 quiet miles. |
| **Burned** | Cracked and smoking | They know it's fake. The plate's own family **hunts** you and everyone else treats you as hostile. Swap it now. |

- **Heats it up:** hurting the family you're pretending to be · saying no to a family favor · failing or ignoring the Nod (2.9) · a search that finds the wrong cargo · a hitchhiker who snitches.
- **Burns it instantly:** being **seen** putting it on. Word travels, and Nora will mention it on the radio.
- **Cools it down:** quiet miles · doing a job for that family (instantly Clean) · passing the Nod · paying **Inky** to re-stamp a burned plate.

### 2.4 How the road reacts to you

Every NPC belongs to a faction. When one notices your car, it reads the plate and picks one reaction:

| The plate they read is… | Reaction | What it looks like |
|---|---|---|
| Their own family's | **Family** | Wave you through, discounts, favors, jobs, the Nod |
| A rival family's | **Rival** | Tail you, box you in, ambush, spin you out |
| A neutral family's | **Neutral** | Ignore you (maybe charge a toll) |
| A Fed plate, and they're a gang | **Law** | Small groups scatter. Big setups open fire. |
| A gang plate, and they're Feds | **Pull-over** | Lights, siren, trunk search |
| A civilian plate | **Shakedown** (gangs) / **Ignore** (Feds) | "Road tax. Pay up or step out of the car." |
| No plate at all | **Suspicious** | Everyone follows you. Feds pull you over. |
| Burned, their own family's | **Hunt** | They chase you down the road |
| Burned, anyone else's | **Hostile** | They attack |

Who counts as a rival is one small table (see [Default relations](#default-relations)), and it can change every run (see 3.4, *Tonight's Word*).

Everyone reads plates, **including you.** Every family's plate has its own color, so you can tell who's who at a glance, and your rear-view mirror shows the plates behind you.

### 2.5 Swapping and witnesses

- Stop the car, walk to the back, **hold E for 3 seconds** (tap-and-hold on mobile). Screwdriver sound, satisfying clunk.
- Anyone who can see you gets an **eye icon** over their head. If an eye is open when the swap finishes, **the new plate is Burned.**
- Your own car blocks line of sight, so park it between you and the witnesses.
- **Safe spots** (nobody ever sees): tunnels, underpasses, the car wash, garages, behind billboards, **Rosa's parking lot** ("At Rosa's, nobody saw nothing."), and **dust storms**. When the storm rolls in, everyone's blind.
- In a crew, a friend can **keep watch** (sees eyes from farther away) or **distract** a witness (honk, chat, throw a bottle).

### 2.6 Where plates come from

| Source | What you get |
|---|---|
| Wrecks and abandoned cars (glovebox, trunk, bumper) | Random plates, Clean |
| A car you knocked out in a fight | Its plate, but **Warm** (they'll notice their guy is missing) |
| Family jobs | Clean, often **Ranked** |
| **Inky's Junkyard** (Mile 10) and his tow truck | Buy, forge, re-stamp |
| Pink-slip races at Redline Pass | Your plate against theirs; the winner keeps both |
| Hitchhikers | Some give you theirs as a thank-you (often Story plates) |
| Your own old wreck (see 3.6) | The plate you went down with |
| Scrappers | They steal plates, and you can steal them back |

### 2.7 Kinds of plates

| Kind | Example | What's special |
|---|---|---|
| **Common** | `MRT-4471` | A standard family plate. |
| **Ranked** | `MRT-CAPO3` | A made member's plate. Heats up slower, opens that family's shortcut and back doors, gets better jobs. |
| **Story** | `NICO-19`, `KRD-001` | One of a kind. Comes with a card (who owned it) and a **hook**: wear it at the right place and a scene plays. Five of them are **Heist Plates**, the clues to the season mystery (6.4). |
| **Vanity** | `NOT A COP`, `MOMS CAR` | Joke plates with joke effects (Appendix A). |
| **Hot** | `13` | The heist plate. Everybody hunts it; everything pays ×3. For maniacs and streamers. |
| **Home** | `LUCKY-7` | Your Runner's real plate. Starts **Wanted** by whoever is after you. Arrive wearing it for your Runner's own ending. |

**Every Story plate is a question.** The card for `NICO-19` says: *"Nico Moretti's car. Found empty in the desert with the keys still in it."* What happens if you wear it into Rosa's diner, his grandmother's place? You'll find out next run. That question is what gets people to start another run.

### 2.8 Tricks that fall out of the rules (no extra systems)

- **Lights off.** At night your plate is lit by its little plate lamp. Kill your lights and nobody can read you from far away, but you can barely see the road, and Sheriff Buck will ticket you for it.
- **Dress the part.** Playing a family's radio station while wearing their plate cools Cover faster. Blasting a rival station with the windows down warms it.
- **Family in the back seat.** A hitchhiker from a family vouches for you: your Cover with them heats up half as fast.
- **Shortcuts.** Each family owns a gated shortcut (the vineyard road, the mountain tunnel, the rail bridge, the Fed service road). The gate opens for their plate. You skip miles and danger, and the loot along them.

### 2.9 Mastery layers (unlock later, not needed for version 1)

**The Nod.** Sometimes a family car pulls alongside and honks a pattern, like *honk · honk · hooonk*. You have to answer the family way:

| Family | The answer | The saying |
|---|---|---|
| Moretti Family | Repeat it exactly | "Respect the old ways." |
| Kuroda-kai | Repeat it **backwards** | "Check your mirror." |
| Nine Lanterns | Repeat it **plus one extra short honk** | "Always pay a little extra." |
| Task Force 13 | Don't honk. **Flash your lights once.** | "Cops don't honk." |

Right answer: Cover goes Clean, and they toss you something (cash, fuel, a tip about the road ahead). Wrong answer or no answer: Warm. Nobody explains the rules; you pick them up from Nora's song dedications, family passengers and notes in gloveboxes. Once you know them, you feel like a made member forever.

**The Two-Faced Car.** Inky sells a **front plate bracket.** Now your car wears two plates:

- People **ahead** of you (roadblocks, checkpoints, oncoming cars) read the **front** plate.
- People **behind** you (tails, chases) read the **back** plate.

Fed plate on the front for the checkpoint, Kuroda plate on the back for the racers tailing you. But if anyone sees both (an agent walks around your car, someone pulls up level with you), it's **"Two-faced!"** and both plates burn.

It's a simple rule that opens up a lot of play, and it's also how the heist was pulled off (6.5).

### 2.10 One event, five scenes

You write each event once, with five short outcomes. This table is the whole production trick:

| Event (gang-run) | Their plate | Rival plate | Fed plate | Civilian / none | Burned |
|---|---|---|---|---|---|
| **Broken-down car** | They ask for a tow: cash + a favor owed | It's a trap: ambush | They panic and run, leaving the trunk open | They ask for a ride | They recognize the plate: chase |
| **Roadblock** | Waved through | Fight, or find a detour | Small: they scatter. Big: firefight | Toll: pay or fight | Spike strips |
| **Gas station** | Family discount, maybe a job | Clerk makes a call: a tail appears a mile later | Clerk is nervous and quietly tips off the family | Normal prices | "We're closed." Ambush in the lot |
| **Car pulls alongside** | The Nod | They ram you | They drop back and tail you | They pass | They open fire |
| **Hitchhiker (family member)** | Hops in and vouches for you | Refuses, or robs you | Refuses and calls it in | Hops in, eyes your glovebox | Runs |
| **Diner** | Free pie and gossip | Room goes quiet; a fight waits outside | Someone slips out the back (follow them for loot) | Normal | Someone makes a phone call |

Fed-run events flip it: a Fed plate is "their plate", and a gang plate means a pull-over.

---

## 3. The Run: 100 Miles, One Night

### 3.1 Shape of a run

- **Mile 0, Cinder Motor Court** (the lobby): pick your Runner, your car and the plates in your glovebox. Park in a numbered spot with your crew to start.
- **Miles 0–100:** five stretches of road, each run by a different power, each with its own landmarks.
- **Mile 98, The Lookout:** a quiet cliff over the sea, and the last safe place to swap. *Who do you want to be when you get there?*
- **Mile 100, Port Solace:** the pier, the lighthouse and the ferry at sunrise. The plate you arrive with decides who's waiting.
- **The sky is the progress bar.** Golden hour at Mile 0, midnight at Rosa's (Mile 50), sunrise at the pier. There is **no timer.** The night only moves when you drive.

### 3.2 The five stretches

| Miles | Stretch | Time and look | Who runs it | Landmarks |
|---|---|---|---|---|
| 0–20 | **The Flats** | Golden hour, dust, tumbleweeds | Sheriff Buck, Scrappers, bikers | **Inky's Junkyard** (10) · **Colter's Speed Trap** (18) |
| 20–40 | **Vineland** | First stars, orchards, neon diner signs | Moretti Family (Mafia) | **Palms Motel** (25, safehouse) · **Starlight Drive-In** (35) |
| 40–60 | **Redline Pass** | Night, hairpins, tunnels | Kuroda-kai (Yakuza) | **Pit 44** (44) · **The Hairpins** (45) · **Rosa's** (50, midnight, neutral ground, safehouse) |
| 60–80 | **Lantern Row** | Deep night, rail yards, fireworks | Nine Lanterns (Triad) | **Lantern Fireworks Co.** (70) · **The Rattlesnake** (75, biker bar, safehouse) |
| 80–100 | **The Last Stretch** | Pre-dawn fog → sunrise, sea cliffs | Task Force 13 (Feds) + everyone | **Solace Bridge Roadblock** (95) · **The Lookout** (98) · **The Pier** (100) |

- **The Flats is the tutorial:** low stakes, first plates, your first swap in your first dust storm, and Sheriff Buck as an easy first boss.
- **The Last Stretch is the border**, like the wall in *Road 96*. Task Force 13 has sealed the county, and **Solace Bridge** is the final exam. Everyone gets the full treatment there: agents walk around the car (a two-faced car gets caught), search the trunk, and give you the Nod. Pass clean, pay your way with a Marker or a friend's help, or ram the barricade and run for it.
- Each stretch has a home family, but patrols are a **mix** drawn from the Turf Map (8.3). *"Lots of Kuroda cars in Vineland tonight"* means no single plate is safe everywhere. Graffiti on the mile-marker posts tells you who holds the next mile.

### 3.3 What you meet on the road

Every 2–4 miles the road deals something from that stretch's deck:

- **Stops** (you choose to pull over): gas station, diner, motel, wreck, junkyard, overlook, roadside stand, family front business (car wash, bakery, tuning garage, teahouse), payphone, Scrapper camp.
- **Encounters** (they come to you): roadblock, checkpoint, plate-scanner pole, a tail, an ambush, a race challenge, the Nod, a speed trap, a dust storm.
- **Hitchhikers:** thumb out on the shoulder. Pick them up or don't.
- **Forks** (2–3 per run): **Highway** (fast, patrolled) · **Old Road** (slow dirt, more loot, more Scrappers) · **Family shortcut** (only opens for their plate).
- **Safehouses** (Miles 25, 50, 75): bank your plates and cash so you keep them even if the run goes wrong. Push on with everything, or bank it now?

You can always see trouble coming if you pay attention: road signs ("CHECKPOINT 2 MI"), Nora's traffic reports, graffiti on the mile markers, and later the police scanner.

### 3.4 Tonight's Word

At the start of every run Nora reads the news. One line changes the whole night:

| Tonight's Word | Effect |
|---|---|
| **War Night** | Two families are at war: double patrols on their turf, stricter Nods. |
| **The Truce** | The gangs won't fight each other tonight. They're all looking for Runners instead. |
| **Budget Cuts** | Half the Fed checkpoints are closed. |
| **Crackdown** | A plate scanner every 5 miles. |
| **Dust Season** | Three times the dust storms: more free swaps, more Scrappers. |
| **Festival of Lanterns** | Fireworks all night. Lantern plates are welcome everywhere, and the smoke hides swaps. |
| **Blackout** | County power is out. Plates can only be read up close. |
| **Plate Shortage** | Wrecks drop twice the plates; Inky charges twice as much. |
| **Full Moon** | The Dust Devils ride tonight: bikers everywhere, looking for a race. |
| **Voss Is Watching** | The Task Force helicopter patrols the whole road. |

### 3.5 When it gets loud

- **Knockouts, not kills.** Enemies drop with dizzy stars; cars smoke and stall. No blood.
- **From the car:** ramming, crewmates shooting or throwing from the windows, trunk gadgets (spike strip, oil slick, smoke).
- **On foot:** bat, crowbar, tire iron, pistol, shotgun, plus each family's signature weapon (see 5).
- **Down?** Crewmates can revive you. If the whole crew is down, you're **Taken** and the run is over.

### 3.6 How a run ends

| Ending | How | Epilogue card |
|---|---|---|
| **Made it** | Reach Mile 100 | Depends on your plate and your Runner (6.7) |
| **Wrecked** | Car destroyed and nobody can fix it | *"Penny's wagon burned out at Mile 64. The Lanterns kept the plates."* |
| **Taken** | The whole crew is knocked out | *"Mags was taken by the Kuroda-kai at Mile 47. Kenji didn't say a word."* |
| **Busted** | Arrested by Task Force 13 | *"Dutch was booked at Mile 88. Agent Voss sends his regards."* |

**The road remembers.** Your car stays where it died. Next run you'll pass your own wreck at that mile, with the plate you were wearing still screwed on.

- **You always keep:** every plate you found (in your **Plate Book**), every story scene you saw, every badge.
- **You keep only if you bank it** (at a safehouse or Mile 100): the actual plates (for your **Plate Wall** and future gloveboxes) and your cash.

### 3.7 A run in two minutes

> **You're Lucky.** Your Home Plate, `LUCKY-7`, is wanted by the Moretti Family. You delivered pizzas to the Sit-Down and they think you saw too much. In your glovebox: a Lantern plate and a Fed plate you bought from Inky.
>
> **Mile 0.** Golden hour. Nora on the radio: *"Tonight's word: the Morettis and the Kuroda-kai are at war. Stay out of the middle, sugar."*
>
> **Mile 6.** A wreck on the shoulder. In its glovebox: a Moretti plate, `MRT-2291`.
>
> **Mile 12.** Dust storm. Nobody can see a thing, so it's a free swap. `MRT-2291` goes on.
>
> **Mile 23.** Vineland. Black sedans everywhere. One pulls alongside: *honk · honk · hooonk.* You honk it right back, exactly; the Morettis respect tradition. The driver nods and tosses a gas can into your back seat.
>
> **Mile 31.** A Moretti capo at a bakery asks you to take a cake box to Rosa's. You're wearing his family's plate, so saying no would look strange. The box goes in the trunk.
>
> **Mile 41.** Redline Pass. The Kuroda-kai see a Moretti plate in the middle of a war. Three coupes come at you on the climb. You make the tunnel, stop in the dark, and put on the Fed plate.
>
> **Mile 42.** You come out of the tunnel as a Fed. The coupes brake and scatter. Nobody picks a fight with a Fed on a small road.
>
> **Mile 47.** A Task Force checkpoint. Salutes, and a friendly agent who'd like to "help you with that trunk." The cake box. No hidden compartment. Floor it and burn the plate? Bribe him? Or let him look? You let him look. It's… cake. Agent Birch laughs: *"Somebody likes you, kid."*
>
> **Mile 50.** Midnight at Rosa's. Nobody reads plates here. You hand over the cake and Rosa cuts you a slice. In the corner booth, a nervous kid asks for a ride. His name is Nico.
>
> *Fifty miles to go. Lantern Row is next, and you've got one Lantern plate left.*

---

## 4. The Car

### What you watch

*Road 96* kept it to two meters. We allow ourselves three:

- **Fuel:** the soft clock. Gas stations are family-owned, so the price depends on your plate.
- **Cash:** tolls, bribes, fuel, repairs, plates.
- **Condition:** three parts, **Engine, Tires, Body.** Crashes and fights wear them down; scavenged parts and garages fix them.

Plus the Cover on your plate, and your own health when you're on foot.

### Storage

- **Glovebox:** spare plates. 2 slots to start.
- **Trunk:** cargo and loot in a small grid. This is what searches look at.
- **Seats:** driver + 3. Crewmates first; hitchhikers fill the rest.

### Upgrades (bought in the lobby, kept forever)

| Upgrade | What it does |
|---|---|
| Bigger glovebox | 2 → 3 → 4 plate slots |
| Quick-release screws | Swap in 1 second instead of 3 |
| Hidden compartment | 2 trunk slots that searches can't find |
| Police scanner | Shows Fed checkpoints and scanners 2 miles early |
| CB radio | Hear family chatter: tails, ambushes, hints for the Nod |
| Front plate bracket | The Two-Faced Car (2.9). Unlocks after Inky's second scene. |
| Reinforced bumper · run-flat tires · bigger tank | The usual |

### Cars

| Car | Feel | How to unlock |
|---|---|---|
| **Old Faithful** (station wagon) | Big trunk, slow, tough | Starter |
| **Consul** (sedan) | Balanced | Complete the Moretti plate set |
| **Kaze GT** (coupe) | Fast, drifty, fragile, 2 seats | Complete the Kuroda set, or beat Kenji |
| **Lucky Van** (delivery van) | Huge trunk with 2 hidden slots, slow | Complete the Lantern set |
| **Retired Cruiser** (ex-cop car) | Gangs flinch until they read the plate | Complete the Task Force set |
| **Mule** (pickup) | Toughest; crew in the bed can shoot (and be shot) | Impress Big Sue |
| **The 13** | The getaway car. Two-faced from the factory. | The true ending |

---

## 5. The Factions

### Plate colors (readable at a glance)

| Faction | Plate |
|---|---|
| Moretti Family (Mafia) | Black with gold letters |
| Kuroda-kai (Yakuza) | White with green letters and a red dot |
| Nine Lanterns (Triad) | Red with gold letters, lots of 8s |
| Task Force 13 (Feds) | White with blue letters and a gold seal |
| San Polvo County (Sheriff) | Tan with brown letters |
| Civilian | Sun-faded yellow with a cactus |

### The Moretti Family (Mafia): "Family eats first."

- **Turf:** Vineland: orchards, a bakery, a car wash ("we clean everything"), the Starlight Drive-In.
- **Wear their plate:** they wave you through, invite you to dinner and ask favors. They expect you to say yes.
- **Wear a rival's:** black sedans wait on the shoulder with their lights off, then box you in three at a time.
- **Job, "The Delivery":** take a cake box to Rosa's without anyone searching it. *"It's cake. Don't ask."*
- **Signature:** drum-magazine SMG · black sedans · crooner and swing radio (*KMRT, The Sunday Gravy Hour*).
- **Set piece, Starlight Drive-In:** a movie is playing and a meeting is happening in the back row. Watch the movie with your crew, slip behind the screen to swap, or start the fight right as the explosions go off on screen.
- **People:** Don Sal Moretti (the boss), Rosa Moretti (his mother), Nico Moretti (his son).

### The Kuroda-kai (Yakuza): "Hold your line."

- **Turf:** Redline Pass: hairpins, tunnels, and Pit 44, a neon tuning garage.
- **Wear their plate:** race invites, escorts through the pass, cheap tuning at Pit 44.
- **Wear a rival's:** their racers try to spin you out on the hairpins.
- **Job, "The Line":** win a race down the pass. Pink-slip rules: your plate against theirs.
- **Signature:** katana (dash strike) · tuned coupes · city-pop synth radio (*Midnight Drift FM*).
- **Set piece, The Hairpins:** a downhill race or chase at night, headlights snaking through the switchbacks.
- **People:** Oyabun Takeshi Kuroda (the boss, rarely seen), Kenji "Redline" Kuroda (his son).

### The Nine Lanterns (Triad): "Every debt is remembered."

- **Turf:** Lantern Row: rail yards, warehouses, a night market by the tracks, the fireworks factory.
- **Wear their plate:** they give you **Markers** (*"we owe you one"*). Call one in from any payphone: a van blocks the road behind you, a clean plate appears under a bench, a tow truck shows up.
- **Wear a rival's:** they don't fight fair, because they're the information family. Firework traps, spike strips, fake detour signs, and motorbike couriers who tag your plate (it goes Warm) and sell your location.
- **Job, "Collect":** pick up three envelopes from three stops before Ivy gets there.
- **Signature:** firework launcher, firecracker stuns · vans and motorbikes · disco and funk radio (*Lucky 8 FM*).
- **Set piece, Lantern Fireworks Co.:** sneak through the factory, or blast through it while the whole sky goes off.
- **People:** Madame Wen (the boss), Ivy Lam (courier).

### Task Force 13 (Feds): "Nobody's clean on Route 13."

- **Turf:** everywhere, strongest in the Last Stretch. Checkpoints, plate-scanner poles, a helicopter.
- **Wear their plate:** checkpoints salute you and small gangs scatter, but the big gang set pieces now want you dead. And **scanners check Fed plates against the roster**: a common fake Fed plate goes Warm every time you pass one.
- **Wear a gang plate:** you get pulled over and searched. The wrong cargo in the trunk means trouble.
- **Scanners:** poles with red lights. A Burned plate starts a chase; a Warm one gets a car sent to take a look.
- **Job, "The Tip":** plant a tracker on a gang car without getting caught.
- **Signature:** taser, flashbang, riot shield · black SUVs, spike strips, a searchlight helicopter · the police scanner (dispatch chatter is free intel).
- **Set piece, Solace Bridge Roadblock (Mile 95):** the last wall between you and the sea.
- **People:** Special Agent Harlan Voss (the boss), Agent June Birch (his partner).

### Wildcards

- **Dust Devils MC (bikers):** *"Plates are for cages."* They don't read plates at all; they judge your **driving** (speed, jumps, near misses). Impress them and they ride with you for 5 miles and scare everyone else off. Boss: **Big Sue**. Hangout: The Rattlesnake (Mile 75).
- **Sheriff Buck Colter:** small town, small time, very bribable. Speed traps in the Flats, tan county plates. Comic relief and the tutorial boss.
- **Scrappers:** desert scavengers in rusted buggies. They swarm cars that sit still too long or take the Old Road, and they rip off parts, **including your plate.** This is the zombie slot from *a dusty trip*. Want real zombies? Reskin them for a Halloween event: *The Dust Dead*.
- **The Hounds:** bounty hunters. They show up once you've burned two plates in one run, work for anybody, and never get tired.

### Default relations

Rows are the faction doing the reading; columns are the plate they read. *Tonight's Word* can change these for a night.

| Reader ↓ / Plate → | Moretti | Kuroda | Lanterns | Task Force | Civilian |
|---|---|---|---|---|---|
| **Moretti** | Family | Rival | Neutral | Law | Shakedown |
| **Kuroda** | Rival | Family | Rival | Law | Shakedown |
| **Lanterns** | Neutral | Rival | Family | Law | Shakedown |
| **Task Force** | Pull-over | Pull-over | Pull-over | Family | Ignore |

**A note on respect:** build these families out of style and code (cars, music, mottos, rules), never out of accents or caricature. Give each one people players love (Rosa, Kenji, Ivy, Birch) and people they love to hate.

---

## 6. The Story

### 6.1 The premise

Nora's intro, first run:

> *"Evening, San Polvo. This is Nora on Dust FM, thirteen-point-oh, and if you can hear me, you're still on the road.*
>
> *Thirteen nights ago somebody walked out of the Sit-Down with the Pot and the Ledger. Nobody saw a face. Everybody saw the plate: thirteen.*
>
> *Now every family in the county is reading every plate on Route 13, and there's only one way out: a hundred miles of desert to Port Solace, where the ferry leaves at sunrise.*
>
> *So wear the right one, sugar. This next song's for everybody running tonight."*

**What happened.** Once a year, the four powers of San Polvo County (the Moretti Family, the Kuroda-kai, the Nine Lanterns and Task Force 13) hold **the Sit-Down**: one table, one night, where they split Route 13 between them. Miles, gas stations, pier slots. This year it was at the Starlight Drive-In. Halfway through, the projector died and the lights went out. When they came back on, **the Pot** (all the money on the table) and **the Ledger** (Agent Voss's black book of every bribe ever paid on Route 13) were gone. A car tore out of the lot. Nobody saw the driver. Everybody saw the plate: **13**.

Now the truce is dead, every family blames another, Task Force 13 has sealed the county, and every car on Route 13 is a suspect.

**You're a Runner:** someone with a reason to leave tonight. You're not the thief. Probably.

### 6.2 Runners

A different person every run, like the teens in *Road 96*. Each has a reason to run, a Home Plate, a perk, three personal scenes spread across runs, and a **Home ending**: reach Mile 100 wearing your own plate.

| Runner | Why they're running | Home Plate | Wanted by | Perk | Unlock |
|---|---|---|---|---|---|
| **Lucky** | Delivered the pizzas to the Sit-Down. Saw the lights go out. | `LUCKY-7` | Morettis | **Beginner's Luck:** the first time a plate would burn, it only goes Warm | Starter |
| **Gia** | Mechanic. Her garage burned on the first night of the war. | `GIA-GRG` | Nobody (civilian, so expect shakedowns) | **Grease:** 1-second swaps, faster repairs | Meet her at Inky's |
| **Mags** | Getaway driver who quit the Kuroda-kai. "Broke the line." | `MAGS-00` | Kuroda-kai | **Wheelman:** better grip, drift boost | Beat her in a race at the pass |
| **Penny** | Kept the Lanterns' books. Knows where the money went. | `PNY-208` | Nine Lanterns | **Books:** 20% off everything; sees what every plate is worth | Give her a ride to Mile 75 |
| **Dutch** | Task Force informant who stopped informing. | `DTCH-4` | Task Force 13 | **Rat:** knows which plates the scanners are looking for | Get Busted once |
| **Juke** | Played in the band at the Sit-Down. Everyone thinks the band was in on it. | `JUKE-BX` | Everybody (hard mode) | **Encore:** busk at stops for cash; once per stretch, freeze a fight for 5 seconds with a song | Reach Mile 100 three times |
| **???** | Drove the 13. | `13` | Everybody, forever | ??? | The true ending |

### 6.3 The regulars

Like *Road 96*'s recurring characters, they turn up at random miles in random runs, but their story always moves forward in order. Every beat is a short scene with a choice.

**Nora Vale.** Night DJ on Dust FM, broadcasting from the old lighthouse at Port Solace. The voice of every run.
1. Narrates your night; her song dedications hide hints.
2. After a few runs she starts talking to *you*: *"This one's for the Runner in the green wagon…"*
3. Asks you to bring her the cut film reel from the Drive-In.
4. At Mile 100 you finally meet her, in the lighthouse at dawn. In the finale she offers to put the Ledger on the air.

**Rosa Moretti.** The Don's mother. Runs Rosa's at Mile 50. *"No guns, no plates, no business at my counter."*
1. Pie, and a rule: nobody snitches at Rosa's.
2. Asks you to find her grandson, Nico, who keeps running away.
3. Admits she has paid "a man in sunglasses" for years to keep Nico out of prison.
4. Her jukebox hasn't played in thirteen days. She asks you to fix it.

**Nico Moretti.** The Don's son. Hitchhiking, always nervous, always leaving.
1. Needs a ride to Rosa's. Won't say why.
2. The Kuroda-kai chase him through the pass. "A misunderstanding."
3. *"I drove something I shouldn't have."*
4. Tells you the whole truth (6.5) and rides shotgun in the finale.

**Kenji "Redline" Kuroda.** Heir of the Kuroda-kai. Fast, proud, loud.
1. Challenges you to a race.
2. Sees you wearing `KRD-001`, his father's first plate, and loses it.
3. The Kuroda-kai are blamed for the heist because of that plate. He wants the truth.
4. His racers block Voss's SUVs at Solace Bridge.

**Ivy Lam.** Lantern courier on a red motorbike. Your rival on the road.
1. Beats you to a wreck and takes the loot.
2. Gets ambushed. Save her or drive past.
3. On the night of the heist she was told to leave a van, keys in it, behind Rosa's, and not to ask why.
4. If you helped her, her bikes run interference in the finale. If you didn't, she sells you out.

**Special Agent Harlan Voss.** Head of Task Force 13. Aviators, helicopter, too many teeth.
1. *"Just a routine check."* Charming.
2. Seems to know every plate you've worn. Unsettling.
3. If you carry a Heist Plate, his helicopter follows you.
4. Waits at the pier if you arrive as a Fed, and at the bridge if you don't.

**Agent June Birch.** Voss's rookie partner. Honest, which is a problem.
1. Lets you off with a warning; asks odd questions about her boss.
2. Someone stole her car's plate, `BIRCH-1`. Bring it back and she trusts you.
3. Tells you Voss wasn't at the table when the lights went out.
4. Arrive at the pier wearing `BIRCH-1` for the Justice ending.

**Inky Delgado.** Plate forger at Inky's Junkyard (Mile 10). Knows every plate's story.
1. Sells you plates and reads you their cards. Won't stop talking.
2. Offers you a front plate bracket: *"Built one of these before. Once."*
3. Admits he forged the `13` for "a guy in sunglasses."
4. Bring him all five Heist Plates and he tells you everything, which unlocks the finale.

### 6.4 The mystery: five Heist Plates

| Heist Plate | Where you find it | What it proves |
|---|---|---|
| `STAR-1` | The projectionist's van at the Drive-In. Wear it to get into the projection booth. | The film was cut on purpose. The blackout was planned. |
| `KRD-001` | A wreck at the bottom of the Hairpins. | The getaway car had **two** plates: `13` on the back and Oyabun Kuroda's old plate on the front, so the witnesses would blame the Kuroda-kai. |
| `LNT-888` | An abandoned Lantern van in the rail yards. | Someone paid the Lanterns to leave a van behind Rosa's that night. |
| `T13-001` | Under the gravel behind the Drive-In screen (only on a *Blackout* night). | It's Agent Voss's own plate. His car was out back, so he left the table before the lights went out. |
| `13` | The getaway car, half-buried in the dunes near Mile 50. Only visible in a dust storm, and only once you have the other four. | The car itself, and whatever's left in it. |

### 6.5 The truth (spoilers, for you, the designer)

1. **Voss planned the heist.** A war between the families lets Task Force 13 "clean up" San Polvo. Voss keeps the Pot and gets to be the hero.
2. He paid the projectionist to kill the lights (`STAR-1`). He paid **Inky** to build a two-faced car with `13` on the back and `KRD-001` on the front. He paid the Lanterns for a swap van behind Rosa's (`LNT-888`), and he slipped out to the back lot before the blackout (`T13-001`).
3. His driver was **Nico Moretti**, the Don's son, desperate to get out of the family. Voss promised him a ticket on the sunrise ferry.
4. Behind Rosa's, Nico opened the Ledger and found his own grandmother on every page, paying Voss to keep Nico out of prison. He couldn't hand it over. He hid the Ledger inside **Rosa's jukebox** (it hasn't played since), buried the Pot somewhere in the desert, and dumped the 13 car in the dunes.
5. Voss still doesn't know where the Ledger is. Nobody else knows Voss did it.

**Community secret:** the Pot really is buried at one fixed spot along Route 13, with only faint hints (a Dust Devils campfire story, a line in one of Nora's dedications, a mark on one mile post). The first players to dig it up get a badge nobody else can ever get. This is the kind of secret YouTube videos get made about.

### 6.6 The Last Night (the finale)

Inky's last scene unlocks a special run:

- **Nico rides shotgun.** The Ledger is in Rosa's jukebox at Mile 50. Fix the jukebox, take the book, and the music finally starts playing again.
- From Mile 50 on, everyone knows the Ledger is on the road: double patrols, every plate starts Warm, and from Mile 80 Voss's helicopter follows you.
- At **The Lookout (Mile 98)** you make the last swap of the game. **The plate you arrive with decides who's waiting at the pier, and what happens to the Ledger.**

| Arrive wearing… | Waiting at the pier | Ending |
|---|---|---|
| A Moretti plate | Don Sal and Rosa | **The Family's Book.** The Morettis own Route 13. Nico stays home. |
| A Kuroda plate | Kenji and his racers | **Hold the Line.** The Kuroda-kai own Route 13 and clear their name. |
| A Lantern plate | Madame Wen | **Every Debt Paid.** The Lanterns own Route 13, and now everyone owes them. |
| A Task Force plate | Agent Voss | **Clean Sweep.** Voss gets his book back. Nobody's clean; now nobody's free. |
| `BIRCH-1` | Agent Birch | **Justice.** Voss is arrested. The families scatter. It's quiet, for a while. |
| A civilian plate, or none | Nobody. Just the sea. | Throw it in the water (**Let It Go**), or climb the lighthouse to Nora (**Everybody Knows**: every secret goes out on the air). |
| Your Home Plate, with Nico, and Rosa's, Kenji's and Birch's stories finished | Everyone you ever helped | **Sunrise** (the true ending). Kenji's racers, Ivy's bikes, Big Sue's riders and Rosa in her station wagon pull up behind you. Voss is finished. The Ledger burns in the sunrise, and every Runner you've played boards the ferry together. Unlocks the secret Runner. |

**The Count.** When the season ends, the finale ending picked most often across all players becomes canon and decides who holds Route 13 in Season 2 (the Turf Map starts from it). It's *Road 96*'s election, except the whole player base votes by playing.

### 6.7 Everyday endings

Normal runs end the same way. Your plate at Mile 100 decides who takes you across, and that's your reward:

| Arrive wearing | Who takes you | Reward |
|---|---|---|
| A family plate | Their boat. *"You owe us one."* | Big Standing with that family + a Ranked plate |
| A Fed plate | A Task Force escort out of the county | Cash + Fed Standing ("they'll want something later") |
| Civilian or none | The public ferry, alone | A cash bonus, because the honest way is the hardest |
| Your Home Plate | Your Runner's own ending | A Runner story chapter + badge |
| `13` | Everyone on the pier stares. Then the fireworks start. | Legendary badge, forever bragging rights |

Every ending becomes a **postcard** for your wall: *"Lucky reached Port Solace at 6:31 AM wearing a stolen Kuroda plate. The Kuroda-kai never found out."*

### 6.8 Story rules (keep it *Road 96*)

- Scenes are short: 30–90 seconds, 2–3 choices, mostly in the car or at a stop.
- Characters talk while you drive. The road never stops for a cutscene unless you park.
- Every choice changes something you'll see later: a character's next scene, a plate, a Turf Map point, a line on the radio.
- Nora ties it all together. She comments on what you did: *"Somebody swapped plates at the Gas-N-Go by Mile 23. Sloppy, sugar."*

---

## 7. The Chill Layer

- **No timer.** The night only moves when you drive. Park at an overlook for ten minutes and the stars will wait.
- **The radio.** Five stations: **Dust FM** (Nora: chill music, road news, dedications with hidden hints), **KMRT** (crooners and swing), **Midnight Drift FM** (city-pop synth), **Lucky 8 FM** (disco and funk) and the **Police Scanner** (an upgrade: no music, just intel). Use licensed music from the Roblox Creator Store.
- **The sky.** Golden hour in the Flats, neon in Vineland, stars over the pass, fireworks over Lantern Row, fog on the coast, sunrise at the pier.
- **Places just to hang out.** Rosa's (pie heals, pinball, the broken jukebox), the Drive-In (watch a silly one-minute movie with your crew), the Dust Devils' campfire (marshmallows heal, bikers tell Route 13 legends), the Palms Motel pool at midnight, overlooks with a **postcard camera**.
- **Passengers.** They chat, react to the music, fall asleep, argue with each other. *Road 96*'s best moments were conversations, and ours should be too.
- **Mini-games** (short, optional): **Plate Bingo** (the real road-trip game: spot the plates on your card as you drive), a drag race at Pit 44, aiming rockets at the fireworks factory, pie eating at Rosa's, pinball.
- **Jokes.** Vanity plates, Sheriff Buck, the cake box, Nora roasting your driving.

---

## 8. Replayability and Progression

### 8.1 Why people start one more run

| Engine | How |
|---|---|
| **Curiosity** | Every Story plate is a question you can only answer by wearing it somewhere. Every answer hands you another plate. |
| **Collection** | The **Plate Book** (every plate you've found) and the **Plate Wall** (every plate you own). Finish a family's set to unlock their car. |
| **Mastery** | Reading patrols, the Nod, the Two-Faced Car, **Ghost Runs** (100 miles, zero fights, zero burned plates). |
| **Variety** | Runner × Tonight's Word × Turf Map × random stops × which regulars show up × your plates. |
| **Story** | Eight regulars with four beats each, five Heist Plates, one mystery, eight finale endings. |
| **Social** | Co-op crews, trading, the weekly Turf War, leaderboards, the Count. |
| **Mercy** | A failed run always gives you something: new Plate Book entries, story scenes, your own wreck to loot next time. |

### 8.2 What carries over

- Plate Book, Plate Wall, banked cash, cars and upgrades, Runners, story progress, badges, postcards.
- **Standing** with each family, long-term. High Standing: better jobs, more Ranked plates, and your Cover with them cools faster. Low Standing: they hunt you harder. Pleasing one family always annoys another.

### 8.3 Social and live

- **Co-op crew (1–4 per car).** The driver drives. Shotgun handles the radio, the Nod and the talking. The back seats keep watch, shoot and fix things. Anyone can swap the plate, so talk first.
- **Trading.** Common, Ranked and Vanity plates trade in the lobby. Story, Heist and Home plates don't, which keeps the story honest.
- **Weekly Turf War.** Every run's jobs, deliveries and endings add points to the families. Every Monday the Turf Map shifts for everyone: *"The Lanterns took Redline Pass."*
- **Daily.** Plate of the Day (one Story plate that shows up in every run today) and a daily Plate Bingo card.
- **Leaderboards.** Fastest 100 · Ghost Run · Longest Hot Run (miles wearing `13`) · Most plates banked.
- **Badges.** Every ending, every family set, your first Two-Faced swap, the Pot.
- **Seasons** (every 6–8 weeks). A new mystery, a new stretch or family (a traveling carnival crew, a big-city syndicate, a Dust Devils civil war), new plates. Season 1 is *The Sit-Down*.
- **Later.** Other players' wrecks on your road, each with a note picked from a list: *"The pass got me." "Trust no pie."*

### 8.4 Monetization (keep it fair)

- Sell **looks and fun**, not power: paint and rims, vanity plates, horn sounds, radio skins, emotes, private servers.
- Sell exact items, not random plate crates.
- Never sell Story, Heist or Ranked plates, or Cover.

---

## 9. Building It in Roblox

### 9.1 Places and servers

- **Lobby place, Cinder Motor Court:** Runner select, garage, Plate Wall, Inky's stall, the Turf Map board, trading. Crews form by parking in numbered spots.
- **Run place:** each crew is teleported into its own **reserved server** (`TeleportService:TeleportAsync` with `TeleportOptions.ShouldReserveServer = true`). One crew per server keeps NPCs, physics and story state simple.

### 9.2 The road

- **Scale (tune it):** 1 mile ≈ 800 studs, cruising ≈ 90 studs/s, so about 9 seconds a mile and about 15 minutes of pure driving. With stops, a full run lands around 35–45 minutes.
- **Chunks:** build the road from ~200-stud pieces, one pool per stretch. Keep ~10 chunks loaded ahead of the car and delete everything more than ~3 behind. Landmarks are handcrafted chunks at fixed miles (Drive-In 35, Hairpins 45, Rosa's 50, Factory 70, Bridge 95, Lookout 98, Pier 100).
- **Stay close to the origin.** Very large coordinates make physics jittery. Chunks behind you are deleted, so the road can curve back through space it has already freed. Or use a tunnel at each stretch border as a seamless teleport back toward the center.
- **The Director:** each stretch has a weighted deck of stops and encounters. Deal one every 2–4 miles and keep a rhythm (quiet, quiet, trouble, stop…). Weight the patrol factions by the Turf Map and Tonight's Word.
- **The sky clock** is one line: `Lighting.ClockTime = (17.5 + mile * 0.13) % 24`, which gives 5:30 PM at Mile 0, midnight at Mile 50 and 6:30 AM at Mile 100.
- **NPC cars** follow the road's own waypoints. No pathfinding needed.

### 9.3 The plate system is small

Plates are just data:

```lua
-- ReplicatedStorage/Data/Plates.lua
return {
	["MRT-4471"]  = { faction = "Moretti",  tier = "Common" },
	["KRD-001"]   = { faction = "Kuroda",   tier = "Story", heist = true,
	                  card = "Oyabun Kuroda's first plate. Found at the bottom of the Hairpins." },
	["NOT A COP"] = { faction = "Civilian", tier = "Vanity", effect = "Paranoia" },
	["LUCKY-7"]   = { faction = "Civilian", tier = "Home",   wantedBy = "Moretti" },
	["13"]        = { faction = "None",     tier = "Hot",    payout = 3 },
}
```

Reading a plate is a couple of small functions. The car stores its plate IDs as attributes (`Plate`, and `FrontPlate` once it has the bracket), and the server keeps each plate's Cover:

```lua
-- ServerScriptService/PlateReader.lua
local CollectionService = game:GetService("CollectionService")
local Plates = require(game.ReplicatedStorage.Data.Plates)
-- Relations[reader][plateFaction] = "Rival" | "Neutral" | "Law" | "PullOver" | "Shakedown" | "Ignore"
-- Rebuilt at the start of each run from Tonight's Word.
local Relations = require(script.Parent.Relations)

local PlateReader = {}

-- Which plate can this viewer see? (Two-Faced Car: people ahead see the front plate.)
function PlateReader.visiblePlate(car: Model, viewerPos: Vector3): string?
	local pivot = car:GetPivot()
	local ahead = pivot.LookVector:Dot(viewerPos - pivot.Position) > 0
	if ahead and car:GetAttribute("FrontPlate") then
		return car:GetAttribute("FrontPlate")
	end
	return car:GetAttribute("Plate")
end

-- How does an NPC from faction `reader` react to that plate?
function PlateReader.reaction(reader: string, plateId: string?, cover: string?): string
	if plateId == nil then return "Suspicious" end
	local plate = Plates[plateId]
	if plate.tier == "Hot" or plate.wantedBy == reader then return "Hunt" end
	if cover == "Burned" then
		return if plate.faction == reader then "Hunt" else "Hostile"
	end
	if plate.faction == reader then return "Family" end
	return Relations[reader][plate.faction]
end

-- Did any witness see this player doing the swap?
function PlateReader.isWatched(swapper: Model): boolean
	local root = swapper:FindFirstChild("HumanoidRootPart")
	if not root then return false end
	for _, npc in CollectionService:GetTagged("Witness") do
		local head = npc:FindFirstChild("Head")
		if head then
			local toSwapper = root.Position - head.Position
			local facing = head.CFrame.LookVector:Dot(toSwapper.Unit) > 0.3
			if facing and toSwapper.Magnitude < 60 then
				local params = RaycastParams.new()
				params.FilterDescendantsInstances = { npc }
				local hit = workspace:Raycast(head.Position, toSwapper, params)
				if hit == nil or hit.Instance:IsDescendantOf(swapper) then
					return true -- clear line of sight (your car in the way would block it)
				end
			end
		end
	end
	return false
end

return PlateReader
```

- **The swap** is a `ProximityPrompt` on the back bumper with `HoldDuration = 3`. When it fires, the server checks that the car is stopped (`AssemblyLinearVelocity.Magnitude < 1`) and that the plate is really in the crew's glovebox, sets the `Plate` attribute, and burns the plate if `isWatched` returns true.
- **The server owns plates.** Clients only *ask* to swap. Never trust a plate the client sets.

### 9.4 NPCs

- Every NPC has a faction and a tiny state machine: **Idle → Notice → React.**
- Notice range is about 60 studs, or about 25 at night if your lights are off.
- Reactions are reusable behavior presets (Family, Rival, Neutral, Law, PullOver, Shakedown, Suspicious, Hunt, Hostile). Write each one once and use it everywhere.
- Cap active NPCs (for example ~20 cars and ~30 people) and despawn anything well behind the crew.

### 9.5 Saving

- Player data (Plate Book, Wall, cash, unlocks, Standing, story beats, postcards) goes through a session-locked DataStore wrapper such as ProfileStore.
- Turf War: each run server adds up its points and pushes them to a weekly key with `DataStore:IncrementAsync` every few minutes. The lobby reads the totals.

### 9.6 Controls and mobile

- **Driving:** a standard chassis (A-Chassis or a simple custom one).
- **Swapping:** a `ProximityPrompt` hold, which works on touch, gamepad and keyboard for free.
- **Honk and lights:** two big on-screen buttons on mobile (`ContextActionService` touch buttons).
- **HUD:** a dashboard. Odometer, fuel, three warning lights, cash, and the plate itself.

### 9.7 Safety and content

- Knockouts, dizzy stars and smoking cars. No blood, no gore.
- Cargo is cash, cake boxes, film reels, jade statues, fireworks, gold watches and one very important book. No drugs.
- Plate text comes from your own list. If you ever let players design vanity plates, filter the text through `TextService`.
- Pink-slip races bet plates earned in play, never Robux.
- Fill in Roblox's maturity questionnaire honestly; guns and fighting affect your rating.

---

## 10. Build Order (MVP Roadmap)

Build the gimmick first. If swapping plates to get past things isn't fun for one mile, it won't be fun for a hundred.

| Milestone | What's in it | The question it answers |
|---|---|---|
| **M1: One Mile** | One car, a straight road, 3 plates (Moretti, Fed, civilian), one Moretti roadblock, one Fed checkpoint, the swap, witnesses, Cover | Is swapping plates to get past things **fun**? Don't move on until it is. |
| **M2: Forty Miles** | Chunked road through the Flats and Vineland; fuel, cash and condition; wrecks; Inky's; Scrappers; dust storms; 10 events × 5 reactions; the Drive-In | Does the road feel alive, and chill? |
| **M3: A Hundred Miles** | All five stretches, all four families, Rosa's, the Lookout and the pier with plate-based endings, Nora's radio lines, the Plate Book, lobby + reserved servers, saving | Do people want to go again? |
| **M4: The Sit-Down** | Runners, the eight regulars, Heist Plates, the finale, postcards | Do people care about the story? |
| **Live** | Tonight's Word, the Turf War, trading, the Nod, the Two-Faced Car, seasons | Do they come back next week? |

---

## Appendix A: Starter Plates

| Plate | Faction | Kind | Card / effect |
|---|---|---|---|
| `MRT-4471` | Moretti | Common | A family sedan. Waves you through Vineland. |
| `MRT-CAPO3` | Moretti | Ranked | A capo's car. Opens the vineyard shortcut. |
| `NICO-19` | Moretti | Story | Nico's car, found empty in the desert with the keys in it. Wear it into Rosa's. |
| `ROSA-1952` | Moretti | Story | Rosa's first car. Every Moretti bows, and Don Sal pulls you over to ask why you have his mother's plate. |
| `KRD-2210` | Kuroda | Common | A street racer's coupe. |
| `KRD-RED5` | Kuroda | Ranked | Opens the mountain tunnel shortcut. Free tuning at Pit 44. |
| `KRD-001` | Kuroda | Story (Heist) | Oyabun Kuroda's first plate. Kenji will want to know where you got it. |
| `LNT-8128` | Lanterns | Common | A delivery van. |
| `LNT-LUCKY8` | Lanterns | Ranked | Madame Wen invites you in for tea. One free Marker. |
| `LNT-888` | Lanterns | Story (Heist) | The van that waited behind Rosa's on the night of the heist. |
| `T13-0417` | Task Force | Common | A motor-pool car. Scanners check it against the roster, so expect it to warm up. |
| `T13-001` | Task Force | Story (Heist) | Agent Voss's own plate. Agents will salute it. Voss will want it back. |
| `BIRCH-1` | Task Force | Story | Agent Birch's stolen plate. Give it back, or wear it to the pier. |
| `STAR-1` | Civilian | Story (Heist) | The Drive-In projectionist's van. Opens the projection booth. |
| `DUST-DVL` | Civilian | Story | Big Sue's old truck. The Dust Devils ride with you through the whole Flats. |
| `NOT A COP` | Civilian | Vanity | Gangs get paranoid: half think you're a Fed, half laugh and let you go. |
| `MOMS CAR` | Civilian | Vanity | Sheriff Buck always lets you off with a warning. Rosa gives you extra pie. |
| `IM LOST` | Civilian | Vanity | Nobody bothers you, but every fork picks itself. |
| `GHOST` | ??? | ??? | Only ever seen in dust storms. Nobody knows who it belonged to. (Save it for Season 2.) |
| `13` | — | Hot | The heist plate. Everybody hunts it. Everything pays ×3. |

---

## Appendix B: Cast and Places

**People**

| Name | Who |
|---|---|
| Nora Vale | Night DJ on Dust FM (13.0), in the lighthouse at Port Solace |
| Rosa Moretti | The Don's mother; runs Rosa's at Mile 50 |
| Don Sal Moretti | Boss of the Moretti Family |
| Nico Moretti | The Don's son; drove the 13 |
| Oyabun Takeshi Kuroda | Boss of the Kuroda-kai |
| Kenji "Redline" Kuroda | His son and heir; racer |
| Madame Wen | Boss of the Nine Lanterns |
| Ivy Lam | Lantern courier on a red motorbike |
| Special Agent Harlan Voss | Head of Task Force 13; the season's villain |
| Agent June Birch | Voss's honest partner |
| Inky Delgado | Plate forger at Inky's Junkyard |
| Big Sue | Boss of the Dust Devils MC |
| Sheriff Buck Colter | San Polvo County's small-time sheriff |

**Places** (by mile)

| Mile | Place |
|---|---|
| 0 | Cinder: Cinder Motor Court (the lobby) |
| 10 | Inky's Junkyard |
| 18 | Colter's Speed Trap |
| 25 | Palms Motel (safehouse) |
| 35 | Starlight Drive-In, scene of the Sit-Down |
| 44 | Pit 44, Kuroda tuning garage |
| 45 | The Hairpins |
| 50 | Rosa's (neutral ground, safehouse) |
| 70 | Lantern Fireworks Co. |
| 75 | The Rattlesnake, biker bar (safehouse) |
| 95 | Solace Bridge Roadblock |
| 98 | The Lookout |
| 100 | Port Solace: the Pier and the Lighthouse |

**Things:** the Sit-Down · the Pot · the Ledger · the 13 car · Cover · the Nod · Markers · Tonight's Word · the Turf Map · the Count.
