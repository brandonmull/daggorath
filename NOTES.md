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

One core, several audiences. The root `README.md` gives each a labeled door
rather than picking a winner:

1. **Learn RL** — the trainer as a worked example.
2. **Play Daggorath** — the emulated game world.
3. **Build on the library** — `daggorath-gym` as an installable environment.

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

### The spine: the environment was the hard part

**The problem this project solves: Dungeons of Daggorath has no API.** Not a bad
API — none. MAME hands you 64K of anonymous bytes and a keyboard matrix. The game
has no source, no hooks, no state export, no reward, no reset semantics, no
concept that an agent exists. Before a single gradient step is possible, someone
has to answer from the outside:

- Which of 65,536 addresses means "you are here"? (`ram.md`, read against the disassembly)
- How do you know you just died? (`combat-model.md` — reconstructed `D40C`, the damage formula, and both strength-vs-damage pools; the answer is exertion overtaking strength, which is *not* the visible heartbeat)
- Can you even get data out? (15 sandbox experiments: FIFO vs. TCP vs. Unix sockets, `emu.file` failing under sustained writes, torn creature-array reads, whether `require()` works in MAME's embedded Lua)
- How do you *act*, when there's no controller — only typed phrases the game accepts at certain moments? (readiness gating on `displayFunction == 0xCE66`)

**The value: `PPO(...)` is one line. Making a hostile, undocumented, 44-year-old
system observable and controllable is everything else.** Anyone can
`gym.make("CartPole-v1")`. This project is the `make`.

That's the transferable claim, and it's what a hiring manager is actually buying:
integrating with a vendor system that has no docs, instrumenting a legacy service
nobody understands, building a simulation harness where the simulator won't
cooperate. RL is the demonstration; instrumentation is the skill.

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
- *"Is 'no API' literally true? MAME has a Lua API."* Phrase it precisely, because
  the precision is more impressive: MAME gives you bytes and keystrokes. It
  supplies zero meaning. Every semantic signal in this project is authored.

## The README plan

The spine is settled; this is how it lands in the root `README.md`.

### The pitch

This reverses an earlier call to leave the pitch alone. It currently reads "Train
a reinforcement-learning agent to play..." — which frames the project as *an RL
project*, i.e. as its weakest and most generic component. If the spine is "the
environment had to be built," the pitch has to say so, or the spine never reaches
the skimmer.

Target: a Gymnasium environment for a 1982 game with no API, no source, and no
notion that an agent exists — MAME hands over anonymous bytes and a keyboard
matrix, and every signal an agent needs was excavated from the ROM and delivered
as a standard `Env`.

### "What makes this interesting"

Two subsections, in this order.

**The environment was the hard part.** RL tutorials hand you an environment; a
44-year-old cartridge doesn't have one. Three bullets:

- *Meaning from a binary* — reading the disassembly to resolve unknown RAM fields;
  the reconstructed combat model and the shield bug in the original ROM.
- *A transport the emulator survives* — the sandbox verdict: FIFO for state, TCP
  for commands, no external dependencies, no torn reads.
- *Typing as an action space* — no controller; every action is a phrase, dispatched
  only when a readiness signal found in RAM says the game will accept it.

Closing line: the payoff is a 311-line trainer, and everything else exists so
those 311 lines can call `step()`.

**Decisions worth arguing about.** The supporting three, in this order:

- *Fact vs. valuation* — the environment reports what is true and returns reward
  `0.0`. It detects death and the win but prices neither.
- *Reward the margin, not heart rate* — the iconic heartbeat is a trap: attacking
  raises the same exertion counter that being hit does.
- *Mask, never shrink* — marked *(planned)*, because it isn't built.

### What happened to the four candidates

They are demoted to *supporting* decisions — evidence of craft inside the
solution, not the reason the project exists:

1. Fact vs. valuation (env reports facts; reward is a swappable opinion)
2. Reward the margin, not heart rate (exertion rewards combat, not a penalty)
3. Mask, never shrink (curriculum uses masking so `--resume` chains) — not yet built
4. Fidelity over convenience — absorbed into the spine; it *is* the problem statement

Fidelity stops being a bullet: "no API" is only a problem because the world is
real, so fidelity is the premise the spine states, not a separate point.

Candidate 3 was missing from the README entirely — an oversight, and the tell is
diagnostic: the list carried the *unimplemented* decision (masking) and omitted
the *shipped* one (the margin). It needs one clause of setup, since "not heart
rate" is opaque unless you know the game has a heartbeat.

## Next

1. Apply the README plan above — the pitch and the "What makes this interesting"
   section.
2. Correct the stale P1 row in `gym/README.md`: `step()` is no longer unusable —
   reward returns `0.0` rather than raising, `_check_terminated` is implemented,
   and `_check_truncated` deliberately returns `False` because `TimeLimit` is
   external. The `environment.py` class docstring is stale the same way.
3. Implement the curriculum's first stage — `--stage`, `MaskablePPO`, and the
   command mask (`agent/docs/plans/curriculum.md`).

