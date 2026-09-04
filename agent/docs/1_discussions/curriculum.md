# Curriculum

_How the agent is taught: the staged path from a fresh agent to competent play. This is open discussion, not a plan — the course ordering and the first course's reward are under revision, and the questions below must be settled before this returns to `2_plans/`. It supersedes the former `2_plans/curriculum/` plan, whose content is preserved here — with new considerations from `knowledge-and-reasoning.md` added alongside, and the tensions between them made explicit._

The foundation this rests on — how knowledge, memory, reasoning, and skill are distinct, and why knowledge lives in a reusable form rather than in the weights — is [`knowledge-and-reasoning.md`](knowledge-and-reasoning.md).

## The governing habit

The thing the ladder exists to build is **examine before you act**: look in the pack, learn what you have, then base the next command on that. This is not a mechanical requirement — a torch can be pulled and lit without ever examining. It is the behavioral discipline we want the agent to acquire, because everything downstream (equipping, revealing, choosing a torch over a sword) depends on acting on inventory knowledge.

## The idea

A fresh agent confronts 154 command phrases, a dark dungeon, and a reward that only pays after the action that earns it. There is no gradient toward lighting a torch before the agent has lit it, nor toward examining a pack before the agent has examined it. The curriculum resolves this by staging the objective: at each stage the agent is rewarded for one thing, and the commands that do not serve that thing are locked behind it.

## The mechanism

One source drives every curriculum effect: the novelty-flag memory (see `../3_decisions/reward.md`). A flag records the unknown → known transition — the first disclosure of the pack, the first reveal of an object, the first entry into a cell. When a flag flips, three things happen at once: soft shaping (the existing information-gain reward), the unlock spike (a one-shot milestone), and the command mask opening (the commands the new information makes meaningful become selectable). A stage is the condition that chooses which flags are watched, and therefore which commands stand locked.

Command gating is a **mask, never a shrink**: the action space stays `MultiDiscrete([26, 31])`, and locked commands have their logits zeroed each step. Shrinking the space would rebuild the policy head and break the `--resume` chain between stages.

## The ordering under revision

The former plan put torch-lighting first, on the grounds that light is the first mechanical need. The revision is that the first course should be **EXAMINE & equip**, because the habit — examine, learn what you have, then act on it — is the real first lesson, and torch-lighting is a worked example of that habit, not the habit itself.

Two orderings, undecided:

1. **Torch first** (former plan): `EXAMINE → PULL → LOOK → USE`, with EXAMINE bolted on as step one. This teaches the *form* of the habit but not the *substance*: the boot pack is fixed (pine torch + wooden sword), so examining reveals nothing new, and the reward that grades the display flip rewards the action, not the information. Its machine was five states (start / examined / held / looked / lit) paying +1.0 to light, +0.1 per step, −0.1 for no progress.
2. **Examine-and-equip first** (proposed): reward the *disclosure* — the pack becoming visible and its contents then being acted on — so the habit itself is what is learned. Torch-lighting follows as course 2 and reuses the habit.

A third possibility, still exploratory, is that the ordering should not be authored at all: causal-chain learning (see `knowledge-and-reasoning.md`) learns trivial preconditions first and composes upward, which would generate this ladder from below.

## Open questions

- **Holdings potential — what is "valuable"?** A potential over held and packed objects is proposed, but there is no formula, and object power is not on the wire (carried objects ship class/proper/reveal only). Does "good" mean class and proper rarity, revealed-ness, or do we put power on the wire first?
- **Reveal novelty — scoped how?** The reward decision lists reveal novelty as deferred, pending a coefficient and power on the wire to scale by power. Do we ship a power-free version now, or wait for power?
- **The mask — when?** Locking PULL until the first EXAMINE is the syllabus's way to enforce the habit, but masking is the deferred `MaskablePPO` work. Is it part of the first course, or is the first course reward-only?
- **Activation.** Each course's reward is active only during its course, but the stage gate (`--stage`, a wrapper parameter) does not exist yet. Wiring a course's reward unconditionally would fire its penalties on every step of the baseline. How is the boundary expressed before the gate lands?

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../3_decisions/reward.md` | The reward layers, potentials, and the novelty memory |
| `gym/docs/3_decisions/state.md` | The scalar fields the potentials draw from |
| `gym/docs/2_plans/objects.md` | Object attainment and the reveal field |
| `gym/docs/3_decisions/perception.md` | The perception, which carries no novelty flags |
