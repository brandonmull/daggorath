# Daggorath — Working Notes

Scratchpad for big-picture decisions, continued across sessions. Not a spec.

## Settled

One `daggorath` repo holds two packages, side by side at the root:

- `gym/` → the `daggorath-gym` distribution, imported as `daggorath_gym`
- `agent/` → the `daggorath-agent` distribution, imported as `daggorath_agent`

The environment/trainer split survives as an *import* boundary — `daggorath_gym`
imports only gymnasium+numpy — not a folder or repo boundary. The repo root was
hoisted so the whole workspace is the project, and git history was preserved
(the agent was never its own repo, so it entered as new files).

Both packages install editable from the root: `pip install -e gym`, then
`pip install -e agent`.

## Audiences / front doors

One core, several audiences. The root `README.md` gives each a labeled door, now
ordered so the spine's own evidence comes first:

1. **How the environment was built** — the instrumentation and the reverse-engineering.
2. **The trainer as a worked RL example** — the PPO pipeline end to end.
3. **Build on it** — `daggorath-gym` as an installable environment, reward swappable.

The doors sit *below* the argument, not above it. They are navigation, not a
getting-started path — that role belongs to `Quick start`. Leading with the
trainer contradicted the spine, so the instrumentation door leads instead.

Three doors do not conflict with one spine. The doors partition *audiences* —
which path you take through the repo. The spine is a *claim* every door inherits.
Different axes, no tension.

## Portfolio positioning

The project doubles as a portfolio piece for AI/systems engineering, and the root
`README.md` is written for a hiring manager, not a code reviewer. The first
question it has to answer is "what problem does this solve," not "what is clever
inside." An earlier pass ranked internal design decisions — fact vs. valuation,
masking, the survival margin. Those are what an engineer reviewing a diff cares
about. They are not the reason the project exists.

### The spine: a world that didn't exist

**The accomplishment is a contribution, not a hardship.** *Dungeons of Daggorath*
did not exist as a world a machine could enter, and now it does. That is what the
front page leads with — what the project gave, not what it endured. The difficulty
is real, and it comes second, as the challenges along the way.

What was given is two things.

**A world.** The game is now a live environment with defined observation and action
spaces, so a training loop can be pointed at it. Knowledge was never the missing
piece: the author released his source, and the retrocomputing community mapped much
of the memory. What did not exist was anything that could *run* — nothing watched
the game as it played, and nothing could act inside it. The contribution is the
distance between documentation and a running system, which is a familiar line in
any engineering shop: a spec is not an integration.

**An interface worth building on.** Getting an agent to play once is a demo;
whether anyone else can use the result is a design question. The interface was built
against a list of what a person training an agent actually needs — a standard API,
learnable spaces, actions that express the game rather than keystrokes, correct
episode boundaries, the freedom to define the objective, true state for reward
without cheating the policy, and both throughput and the ability to watch.

The list itself is part of the accomplishment. Anyone can enumerate features;
enumerating *needs* and then answering them is the difference between a library and
a one-off. Two needs are still unmet — environment registration and seeding — and
recording that is part of the same discipline.

The load-bearing one is that the environment holds no opinion about what the agent
should want. It reports what is true and returns reward `0.0`, so the objective
belongs to whoever is training. That is "fact vs. valuation" restated as a service
to the developer rather than as an internal architecture note — which is the version
worth leading with, and why the README no longer spends a bullet on it.

**Why this world is worth having.** A new environment on its own invites a shrug —
there are hundreds. The value is in this one's properties. The game keeps no score at
all. The dungeon is dark until a torch is lit, and what cannot be seen is heard. Every
action is one of 806 typed commands. Nothing pays off quickly. Those are sparse
reward, partial observability, a large compositional action space, and a long horizon
— the four conditions modern RL handles worst, and testbeds posing them are scarce.
The game's age stops being a curiosity and becomes the reason it is useful.

State the scarcity flatly on the front page and don't justify it. A reader who doesn't
know why those properties are hard doesn't need teaching — "scarce" includes them in
the conversation in one word.

Then the challenges along the way. MAME hands you 64K of anonymous bytes and a
keyboard matrix and supplies no game meaning at all — no player, no creature, no
wall. Before a single gradient step is possible, someone has to answer from the
outside:

- Which of 65,536 addresses means "you are here"? (`ram.md`, read against the disassembly)
- How do you know you just died? (`combat-model.md` — reconstructed `D40C`, the damage formula, and both strength-vs-damage pools; the answer is exertion overtaking strength, which is *not* the visible heartbeat)
- Can you even get data out? (15 sandbox experiments: FIFO vs. TCP vs. Unix sockets, `emu.file` failing under sustained writes, torn creature-array reads, whether `require()` works in MAME's embedded Lua)
- How do you *act*, when there's no controller — only typed phrases the game accepts at certain moments? (readiness gating on `displayFunction == 0xCE66`)

**The value: `PPO(...)` is one line. Turning a 44-year-old machine into something a
training loop can hold a conversation with is everything else.** Anyone can
`gym.make("CartPole-v1")`. This project is the `make`.

That's the transferable claim, and it's what a hiring manager is actually buying:
taking a system that is documented but inert — a vendor product, a legacy service,
a simulator that won't cooperate — and making it something software can drive. RL is
the demonstration; instrumentation is the skill.

### The evidence

| Component | Size |
|---|---|
| Trainer (`daggorath_agent`) | 311 lines |
| Environment + Lua plugin | 2,387 lines |
| Docs — RE, findings, plans, decisions | 13,111 lines |
| Sandbox experiments answering "will MAME even let me do this?" | 15 |

One caveat to keep straight when talking about this: 5,813 of those doc lines are
`code.md`, a faithful transcription of the published disassembly — source
material, not authored work. The authored reverse-engineering is `ram.md`,
`combat-model.md`, `findings/`, and the sandbox.

### Stress-testing it

- *"Isn't this just 'I reverse-engineered a ROM' — a hobby flex?"* No, and the
  distinction matters: the excavation terminates in a standard interface. A ROM
  hack ends in trivia; this ends in `observation_space`, `step()`, and a
  pip-installable package. That's integration engineering, not curiosity.
- *"Doesn't this undersell the ML?"* It sells it accurately. The trainer is 311
  lines of plain SB3, and the curriculum isn't built yet. Leading with RL would
  lead with the most commoditized, least finished part. Leading with strength is
  not modesty — it's positioning.
- *"Is 'no API' literally true? MAME has a Lua API."* Don't make the claim at all —
  MAME has a Lua API, and the game itself is documented. The precise claim is
  narrower and still strong: MAME gives you bytes and keystrokes and supplies no
  *game* meaning, and nothing that existed could read the game as it ran or act
  inside it.
- *"Didn't the community already do this?"* They did the part they did, and it was
  substantial — the author released his source, and the retrocomputing community
  mapped much of the memory. Both were relied on heavily and are credited in
  `ram.md` and `gym/README.md`. What did not exist was a running system: a live
  channel, an action interface, episode boundaries, an environment. The project also
  gave back — the `??` fields their map left open, the combat math, and the
  emulator-instrumentation findings. Never phrase this as having opened a sealed box.
  It is false, it erases the people the work stands on, and it is the first thing a
  knowledgeable reviewer will catch.

## The README plan

The spine is settled, and this is how it landed in the root `README.md` — applied,
and kept here as the record of why the front page reads the way it does.

### The pitch

Four failed drafts before this one, and every failure is instructive.

The original — "Train a reinforcement-learning agent to play..." — framed the
project as *an RL project*, i.e. as its weakest and most generic component. The
replacement was worse in a subtler way: it opened with a category ("A Gymnasium
reinforcement-learning environment for...") and stacked seven jargon terms before
any value, landing on `Env`, the least evocative word available.

A third pass tried leading with the game's atmosphere — the heartbeat, the dark
maze. That fails too, for two reasons worth remembering: it leads with the
*demonstration* rather than the instrumentation, contradicting "RL is the
demonstration; instrumentation is the skill," and the heartbeat is precisely the
red herring flagged above — the death signal is exertion overtaking strength, not
the audible heart.

A fourth pass produced two more failures worth recording. A generalizable opening —
"legacy systems don't come with APIs" — is a platitude that invites "so what," and
it delays the actual idea by two paragraphs. And a paragraph cataloguing what the
game withholds (no state to query, meaning recovered from memory, actions typed)
is inventory: every fact in it already appears under "What makes this
interesting," so in the intro it is a toll booth the reader has to pay before
reaching the point.

A fifth pass failed on framing rather than wording. "This project makes a sealed,
undocumented program observable and controllable" claims difficulty as the
accomplishment — a statement about what the author endured. The accomplishment is a
contribution: what now exists that didn't. And the words themselves were false. The
author published his source and the community mapped the memory, so "sealed,"
"undocumented," and "no source" were all wrong — wrong in the direction that erases
the people the work stands on.

A sixth pass found the actual claim. The fifth still led with a *player* — "software
can play it now" — which is both weaker and less honest than what exists. A player is
an unfinished outcome, and a scripted bot could claim it without any of this work. The
claim is the *platform*, and the platform is only interesting because of what the game
demands of it.

Settled: the tagline stands alone under the title. Then one paragraph — the game is now
a reinforcement-learning environment and a brutally hard one, the four properties in
plain language, a flat statement that such testbeds are scarce, and the turn that makes
the game's age an asset. It closes on the interface in a single clause. Then one
paragraph of challenge prelude: finishing a memory map others had started, the combat
math, and what an emulator tolerates at full speed.

"A world that didn't exist" is the plain-English replacement for "this project is
the `make`" — same shape, same landing, no insider knowledge required.

Five binding rules for the opening.

**Claim the platform, not the player.** "Software can play it now" is the weaker
claim: an outcome that isn't finished, and one a scripted bot could make without any
of this work. What exists is an environment.

**Credit what came before.** The author's published source and the community's
memory map are load-bearing prior work, relied on heavily. Any phrasing that implies
the game was sealed, closed, or undocumented is false and gets cut.

**The intro states the idea and stops.** Supporting facts belong to the section
that owns them. If a fact already appears under "What makes this interesting," it
does not appear in the opening — two short paragraphs, then `Quick start`.

**No jargon before value.** MAME, the 6809, Lua, Gymnasium, and `Env` do not
appear. They belong in `Quick start` and the doors, where the reader has a reason
to care. The game is named and dated, and that is all the identification the
intro carries.

**No insider references.** `PPO(...)`, `gym.make("CartPole-v1")`, and "this
project is the `make`" all failed for one reason: the punchline only lands if you
already know that a single call hands you a finished training world. To everyone
else it is noise sitting where the climax should be. Those lines stay in *this*
document, whose audience knows the stack, and get translated for the README into
plain terms — normally you download the world; there was none to download.

### "What makes this interesting"

Three subsections, in this order — contribution first, then challenges, then
judgment calls.

**An interface worth building on.** The developer-needs table: a standard API,
learnable spaces, actions that express the game rather than keystrokes, correct
episode boundaries, the freedom to define the objective, true state for reward
without cheating the policy, and throughput plus the ability to watch. Each row
names the need on the left and how it is served on the right. Closing beat: the
environment holds no opinion about what the agent should want. Then the two unmet
needs — registration and seeding — because a needs list containing only solved
needs is marketing.

**What it took.** MAME supplies memory and a keyboard matrix and no game meaning at
all. Three bullets:

- *Meaning from a binary* — reading the community's disassembly to resolve the RAM
  fields its map left open; the reconstructed combat model and the shield bug.
- *A transport the emulator survives* — the sandbox verdict: FIFO for state, TCP
  for commands, no external dependencies, reads gated against mid-update sampling.
- *Typing as an action space* — no controller; every action is a phrase, dispatched
  only when a readiness signal found in RAM says the game will accept it.

Closing line: the payoff is a 311-line trainer, and everything else exists so
those 311 lines can call `step()`.

**Decisions worth arguing about.** Two, not three — *fact vs. valuation* moved up
into the interface section, where it reads as a service to the developer rather than
an architecture note:

- *Reward the margin, not heart rate* — the iconic heartbeat is a trap: attacking
  raises the same exertion counter that being hit does.
- *Mask, never shrink* — marked *(planned)*, because it isn't built.

### What happened to the four candidates

One was promoted, two remain as supporting decisions, one was absorbed:

1. Fact vs. valuation — **promoted**, restated as the developer's freedom to define
   the objective, and now the closing beat of the interface section
2. Reward the margin, not heart rate (exertion rewards combat, not a penalty)
3. Mask, never shrink (curriculum uses masking so `--resume` chains) — not yet built
4. Fidelity over convenience — absorbed into the spine; it *is* the problem statement

Fidelity stops being a bullet: the gap between documentation and a running system
only exists because the world is real, so fidelity is the premise the spine states,
not a separate point.

Candidate 3 was missing from the README entirely — an oversight, and the tell is
diagnostic: the list carried the *unimplemented* decision (masking) and omitted
the *shipped* one (the margin). It needs one clause of setup, since "not heart
rate" is opaque unless you know the game has a heartbeat.

### Structure, and what the spine displaced

Ordering the front page by the reader's questions — what is this, can I install it,
what's broken, why is it interesting, where do I go deeper — moved four things:

- **A `Quick start` now sits directly under the pitch.** The doors are navigation,
  not a getting-started path; the root had no install commands at all.
- **A `Status` section precedes the argument.** The pitch got more assertive, so the
  limitations come first: no trained agent, no curriculum, no gym registration.
- **The doors moved below "What makes this interesting" and were renamed.** Leading
  the reader to the 311-line trainer immediately after arguing that the environment
  was the hard part was self-contradicting. "How the environment was built" now
  leads, and "Build on it" points at the perception and reward plans instead of
  repeating the install link.
- **The `Repo map` table is gone.** Three rows, two of which the doors already
  covered.

## Next

1. Correct the stale P1 row in `gym/README.md`: `step()` is no longer unusable —
   reward returns `0.0` rather than raising, `_check_terminated` is implemented,
   and `_check_truncated` deliberately returns `False` because `TimeLimit` is
   external. The `environment.py` class docstring is stale the same way.
2. Implement the curriculum's first stage — `--stage`, `MaskablePPO`, and the
   command mask (`agent/docs/plans/curriculum.md`).

