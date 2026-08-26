# Curriculum

_How the agent is taught: the staged path from a fresh agent to one that plays competently. This is the trainer's half of the curriculum — selecting a stage, activating the matching reward channels, and masking commands. The environment's half — the perception scaffolding it exposes now and removes later — is documented in the gym package's `perception/plan.md`. Not yet implemented._

## Purpose

A fresh agent confronts 806 commands, a dark dungeon, and a reward that only pays after the action that earns it. There is no gradient toward lighting a torch before the agent has lit it, nor toward examining a pack before the agent has examined it. The curriculum resolves this by staging the objective: at each stage the agent is rewarded for one thing and the commands that do not serve that thing are locked behind it.

## The core mechanism — the novelty flag

One source drives every curriculum effect: the **novelty-flag memory** (see the gym package's `reward/plan.md`). A flag records the unknown → known transition — the first reveal of an object, the first entry into a cell, the first sighting of a creature type. At the moment a flag flips, three things can happen at once:

1. **Soft shaping** — the existing information-gain reward for the transition. This stays; it does the dense credit assignment.
2. **The unlock spike** — a one-shot reward, larger than ordinary discovery, paid specifically when a flag enables a new capability. It marks the milestone.
3. **The command mask opens** — the commands that the freshly-gained information makes meaningful become selectable. A command locked before the transition is masked (its logit zeroed), not removed.

The same flag, three outputs. A stage is the condition that determines which flags are being watched and therefore which commands stand locked.

## Mask, never shrink

The action space is `MultiDiscrete([26, 31])` and is fixed. Locking a command means **masking** it in the policy — zeroing its probability each step while the action space keeps its shape — never shrinking the space.

The reason is architectural: shrinking the action space changes the policy head and therefore rebuilds the network, which breaks the checkpoint chain (`--resume`) from one stage to the next. Masking changes nothing about the network, so a stage transition is a continuation, not a restart.

## The ladder

The stages are ordered; each unlocks the prerequisite for the next.

```
stage 1 — EXAMINE, then equip
    the agent learns what it carries and that the pack matters
stage 2 — LOOK, then light
    the agent learns where it is by lighting the torch
stage 3 — explore
    the agent moves through the dungeon and maps it
stage 4 — survive
    the agent fights when it can win and runs when it cannot
```

### Stage 1 — EXAMINE & equip

The agent discovers its inventory and that holdings are worth improving. The unlock marker is the first disclosure of the pack; the commands that examine and equip the inventory stand behind it.

Reward: a **holdings potential** over the objects held and packed, and **reveal novelty** — the first reveal of each held object. Holdings is listed in `reward/plan.md` as "no — object detection," but the specifier decoding now exists; the potential is available.

### Stage 2 — LOOK & light

The agent discovers the dungeon by lighting the torch. The unlock marker is the transition to illumination; the sight-dependent commands stand behind it.

Reward: a **sight potential** over `effective_light_physical` — illuminated is good — paid when the torch is lit so LOOK actually reveals the maze. This channel is available now: `effective_light_physical` and `torch_minutes` already ship as scalar fields, no object detection required.

### Stage 3 — explore

The agent moves through the dungeon. Marker: new cells entered, salient features discovered.

Reward: **advance** (new cell) and **discovery** (a salient feature — junction, door, dead end). Advance exists; discovery is deferred on a line-of-sight feature extractor.

### Stage 4 — survive

The agent reasons about engagements. This is the hard stage: `player_strength − m0221` teaches "don't die" but not "this creature is beatable." A true fight/run signal needs a threat estimate against the agent's strength — the deferred combat-model work, not a coefficient. This stage is the deferred refinement it already is in `reward/plan.md`.

## Interface

```
python -m daggorath_agent.train --stage 1 --watch
```

- `--stage N` selects the curriculum stage (default 0 — the current baseline reward).
- The stage is forwarded to the reward wrapper at construction, which activates the matching reward channels.
- The command mask is derived from the same stage and the agent's per-episode novelty memory.

## The two responsibilities

### Select the stage and forward it

`make_env()` gains a `stage` parameter and passes it into `DaggorathRewardWrapper`. The reward wrapper gains a matching `stage` parameter; the reward channels active for that stage are the reward side of the curriculum. The training pipeline itself is unchanged — same `PPO`, same `DummyVecEnv`, same `--resume` checkpoint chain.

### Hold and apply the command mask

Command gating is a **mask, not a shrink**: the action space stays `MultiDiscrete([26, 31])`, and locked commands have their logits zeroed each step. This requires the `MaskablePPO` policy (`sb3-contrib`), already a dependency.

- The mask is computed from the current **unlock set** — the novelty flags the stage is watching.
- The unlock set is **episode-scoped** progress and lives alongside the reward's novelty memory, never in the observation.
- At a flag's unknown → known transition: the soft shaping is unchanged, the unlock spike is paid, and the mask opens the commands that the freshly-gained information makes meaningful.

## Composition with persist-learning

Because the action space never changes shape, a stage transition is not a policy rebuild. `--resume` therefore chains stages: train stage 1, checkpoint, resume into stage 2 on top of the learned weights, and so on through the ladder. This is the direct payoff of "mask, never shrink."

## Deferred

- **Automatic graduation.** Advancing stages is manual in the first trainer (`--stage`). A trigger — e.g. the unlock spike for the current stage's flags decaying, or a fixed step budget — is a follow-up.
- **Joint masking.** The INCANT + ring-only constraint is per-object joint masking, not the per-axis template gating of this plan. It remains the separate, already-deferred joint-mask policy.

## Decisions

- **Mask, never shrink.** The action space keeps its shape so `--resume` works across stages.
- **The unlock set is reward-side bookkeeping.** It is valuation progress, never perception.
- **Masking introduces `MaskablePPO` as the policy.** Plain `PPO` cannot express a per-step zeroing of actions.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `docs/game/combat-model.md` | The survival margin and the fight/run foundation |
| `gym/docs/plans/reward/plan.md` | The reward layers, potentials, and the novelty memory |
| `gym/docs/plans/state/plan.md` | The scalar fields the potentials draw from |
| `gym/docs/plans/objects/plan.md` | Object attainment and the reveal field |
| `gym/docs/plans/perception/plan.md` | The perception, which carries no novelty flags |