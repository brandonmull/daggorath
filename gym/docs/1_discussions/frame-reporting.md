# Frame Reporting — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

The state channel is change-gated: it writes a record only when something differs from the last snapshot, and writes nothing at all when nothing changes. This discussion argues that the channel should instead report every frame — a frame number on every frame, the changed content beside it, and an empty frame standing in for "nothing changed."

The reason belongs to the agent side and is argued there in [`causal-attribution.md`](../../../agent/docs/1_discussions/causal-attribution.md): an agent cannot tell what it caused from what the world did on its own unless it observes, with exact timing, both the changes that follow an action and the changes that happen during inaction. Change-gating withholds exactly that record. What follows is the argument for the mechanism the environment must provide — the frame number, the heartbeat, and where the step-unit decision belongs.

## Should the frame number come from the sampler, or be counted by the reader?

The sandbox needs to measure how many frames pass between a command and its effect. Where that count comes from decides whether it can.

> **the observation** — "The frame number still makes sense in other modes. It can still be useful to know how many frames were skipped when you're only receiving periodically."
>
> **the answer** — "Counting on the Python side gives an index into the read stream, not the game. It can't tell you ten frames were skipped, because from Python's seat those ten frames never existed. Only the game knows frames happened — the sampler's counter ticks every frame whether or not anything is written. So the number has to come over the wire, not be counted locally."

A reader can count only what it receives, and a change-gated channel hides the frames between changes. Any count the reader builds is a count of records, not of time. The sampler is the only party that has seen every frame, so it is the one that must say which frame this is.

## Should "nothing changed" be an explicit frame, or silence?

With the frame number settled, the question turns to the frames that carry nothing else. Under change-gating, "nothing changed" is not a message at all — it is silence.

> **the proposal** — "What if we buffered and flushed every frame number regardless of changes, and just left the content blank when no changes occurred?"
>
> **the agreement** — "Nothing changed becomes explicit, not silence. An empty frame is a statement — this frame passed, no change — where change-gating's silence is an absence you have to infer. And a heartbeat that stops means MAME is stuck."

Silence is ambiguous in a way an empty frame is not. A reader that sees nothing cannot tell "the game is quiet" from "the game is stuck or a record was missed." The empty frame resolves that — it says the frame passed and nothing changed — and it doubles as a liveness signal, because a heartbeat that stops is a fault, not a quiet room.

## Should change detection drop the whole frame when quiet, or only the content?

Reporting every frame appears to contradict a settled principle. The project's own overview says the state channel emits a record only when something meaningful changes, never every frame.

> **the doubt** — "Wasn't there an issue with sending state every frame?"
>
> **the answer** — "The issue was sending the state every frame — roughly 154 bytes. Change detection existed because writing that much on every idle frame was wasteful, and a blocked write inside the frame notifier freezes MAME. An empty heartbeat is five bytes. The objection was about bytes, not about frames."

The principle was never about frames; it was about not rewriting the full state when nothing moved. The heartbeat keeps the spirit — content is still change-gated, only what changed is sent — while the frame number, five bytes on an idle frame, costs next to nothing. Reporting every frame does not resurrect the problem the principle solved.

## Should the step-unit be the sampler's setting, or the consumer's choice?

Once the wire carries every frame, the remaining question is how to group those frames into steps. That grouping is where the two consumers diverge.

> **the proposal** — "Maybe we don't need a flag at all. Maybe we always report it, and let the client decide what it does with it."
>
> **the agreement** — "The environment reports at the finest granularity, and the coarser units are the client's business. Frame versus change versus command is the client's decision, not the wire's."

The producer has one job — report every frame, numbered — and every judgment about time belongs downstream. Whether one step is a frame, a change, or a settled command is the question the causal-timing sandbox is measuring, and it is answered by a predicate in the environment's step loop, not by a knob on the sampler. The producer stays uniform; the variation lives in Python.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `../../../agent/docs/1_discussions/causal-attribution.md` | The causal-attribution motivation — the two halves this mechanism serves |
| `extensibility.md` | The open question this answers — whether every-frame reporting is a setting or a record of its own |
| `../2_plans/extensibility.md` | The `report_every_frame` flag this discussion supersedes |
| `../findings/ipc.md` | The FIFO write path and the blocking concern behind change detection |
| `state-verification.md` | The transient question — whether a one-frame change is even catchable |
| `../../../docs/overview.md` | The "change detection, not frame-by-frame" principle this refines |
