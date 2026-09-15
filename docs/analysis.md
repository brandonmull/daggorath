# Analysis by Pi

A full-codebase review of the Daggorath project, written 2026-09-15 and revised the same day after discussion with the author. Scope: both Python packages (`gym/`, `agent/`), the MAME Lua plugin, the tests, and the documentation. Findings are ordered by what matters most for training.

## Overall

The reverse-engineering discipline is impressive: a finished RAM map, a disassembly, a change-detection wire protocol, and perception gates that mirror the game's own visibility rules. The documentation tiering (`1_discussions` → `2_plans` → `3_decisions`, `findings/`, `references/`) is consistent and matches the code. The package split is clean, and the import boundary holds (`daggorath_gym` imports only gymnasium and numpy; training stays in `daggorath_agent`). The PBRS shaping term is correct (`γ·Φ(s') − Φ(s)` with matching γ = 0.99).

A few issues remain, and two of them will matter during training.

---

## 🔴 Correctness

### 1. Episodes have no length limit

`environment.py._check_truncated()` always returns `False`, and `train.py` never wraps the environment in `TimeLimit` or passes `max_episode_steps`. The survival potential makes standing still nearly neutral (it drains only `~0.01·Φ` per step), so an agent can sit still forever and the only terminators are death and the win. An untrained policy that neither attacks nor advances can produce episodes that run indefinitely without a terminal signal.

**Fix:** wrap the environment in `gymnasium.wrappers.TimeLimit(max_episode_steps=N)` inside `make_env()`, or add a custom truncation.

### 2. `reset()` relaunches MAME every episode

`reset()` stops the old `MameOperator` and starts a new one, which means a full subprocess spawn, boot, command-socket accept, and readiness gate each episode. That costs seconds per episode at minimum. The `machine-save-load` sandbox showed that CoCo 2B save states work, so wiring a save-state restore into `reset()` is the largest wall-clock win available for training throughput.

---

## ⏳ The step unit

The environment reports every change it sees, stamped with a frame number, and leaves it to whoever reads the state to decide what counts as one "step." `gym/docs/3_decisions/frame-reporting.md` states this boundary directly: "the step unit is the consumer's choice."

The consumer half does not exist yet. Today `_receive_latest_state()` keeps only the last buffered change, and the reward wrapper scores the jump from the previous kept state to that one. Everything in between is discarded. The design that will replace this is written down:

- `agent/docs/1_discussions/causal-attribution.md` describes the goal: telling "I caused this" apart from "the world does this on its own," by watching what happens after an action and what happens while idle.
- `agent/docs/1_discussions/knowledge-representation.md` describes the shape: separate the action from its effect, wait a short window for the game to settle, then record what changed.
- `agent/sandbox/command-latency/` contains the experiment measuring the timing those two depend on.

The environment is complete as designed. What remains is the agent-side code that groups frames into steps and separates an action from its effect. Until that exists, reward is scored on a lossy transition from the first kept state to the last.

---

## 🟡 Performance

### 3. Lua samples everything every frame, then dedups

`state.lua` `_onFrame()` reads the full 1024-byte maze, 32 creature slots, the object arena scan, 1024 command-area pixels, and the holes and ladders, on every single frame. It compares each result against a snapshot afterward. The dedup saves FIFO bandwidth but not CPU, because the sampling is the expensive part. On a 0.89 MHz emulated CPU that sampling is a real cost to training throughput.

**Fix:** sample the scalar frame every frame, and sample the world channels (maze, objects, creatures, holes) on a slower cadence, since they change far less often than the numeric state.

### 4. `_getMemorySpace()` re-walks all devices every frame

It iterates `manager.machine.devices` on every frame to find `:maincpu`. The code re-acquires on reset via `onReset()`, so caching the space and re-fetching only after a reset would remove a per-frame iteration.

---

## 🟡 RL observation design

### 5. Floor objects mark "empty" with a value that means something real

The floor-object channel marks an empty slot with zeros in all three fields, while `hands` and `pack` mark empty with `0xFF`. Object specifier `0` is a real value (an unrevealed FLASK), so a flask at cell (0,0) would read the same as an empty slot. That corner never holds an object, so the literal collision is theoretical. What remains is a missing occupancy flag (the creature channel has one) and two different empty markers. An unrevealed flask is only "present" because its X/Y coordinates happen to be nonzero.

**Fix:** use `0xFF` as the empty marker, or add an occupancy plane.

### 6. Map channel conflates "unseen" with a value

The map uses `0xFF` (255) to mean "unseen" and packs it into the same planes as edge bytes (0–3) and feature bytes (0–4). The CNN then has to learn that 255 is a visibility marker and not a real value, which is awkward because unseen regions are mostly walls in truth. A third binary plane, a visibility mask, would let the value planes carry clean values.

### 7. γ coupling is implicit

`reward.py` hardcodes `_GAMMA = 0.99` for the shaping term, and `train.py` relies on PPO's default γ also being 0.99. If anyone tunes PPO's discount, the PBRS policy-invariance guarantee silently breaks. Derive the value from the model config, or at least assert and document the coupling.

---

## 🟢 Latent and minor

- **Frame-number bug in `emulator.py recv()`.** It resets `_frame_number` and `_frame_state` at the end of every call even when a partial record remains buffered. A record split across FIFO reads loses its frame-number association (it becomes `None`) and can split one frame into two `recv()` returns. This is harmless today because nothing consumes the frame number, but it will matter once a "wait-for-settle" feature is built on frame gaps.
- **`.gitignore` files use CRLF line endings and no trailing newline.** Harmless, but normalizing them would avoid churn.
- **`heart_rate = 60.0 / interval`.** This assumes `interval` is in 1/60-second units. A one-line comment would document that assumption, since it is not obvious.

---

## What to do first

1. **Add a `TimeLimit`.** It is quick and fixes the unbounded-episode problem.
2. **Wire save-state restore into `reset()`.** The largest training-throughput win.
3. **Reduce the Lua per-frame sampling cadence.** The next-largest throughput win.
4. **Fix the floor-object empty marker.** Quick, but low urgency since the literal collision never happens in practice.

The γ coupling and the map visibility mask are smaller design refinements. The step-unit consumer is the larger causal-attribution effort underway.
