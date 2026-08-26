# Curriculum — Agent Orchestration Plan

_How the training harness drives the curriculum staged in the gym package's `curriculum/plan.md`. This is the trainer half: selecting a stage and masking commands. Not yet implemented._

## Purpose

The environment's curriculum plan defines the stages, the channel table, and the "mask, never shrink" rule. This plan specifies what the trainer must do to run those stages: expose a stage selector, forward it to the reward wrapper, and hold the command mask. It defers the question of automatic graduation.

## Interface

```
python -m daggorath_agent.train --stage 1 --watch
```

- `--stage N` selects the curriculum stage (default 0 — the current baseline reward).
- The stage is forwarded to the reward wrapper at construction, which activates the matching reward channels (see the env curriculum plan).
- The command mask is derived from the same stage and the agent's per-episode novelty memory.

## The two responsibilities

### Select the stage and forward it

`make_env()` gains a `stage` parameter and passes it into `DaggorathRewardWrapper`. The reward wrapper gains a matching `stage` parameter; the reward channels active for that stage are the reward side of the curriculum. The training pipeline itself is unchanged — same `PPO`, same `DummyVecEnv`, same `--resume` checkpoint chain.

### Hold and apply the command mask

Command gating is a **mask, not a shrink**: the action space stays `MultiDiscrete([26, 31])`, and locked commands have their logits zeroed each step. This requires the `MaskablePPO` policy (`sb3-contrib`), already a dependency.

- The mask is computed from the current **unlock set** — the novelty flags the stage is watching (see the env curriculum plan's "novelty flag" mechanism).
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