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

The empty marker was revisited once the reader stopped keeping empty frames. The remaining question was whether the marker's certainty of completeness was worth a report for every quiet frame.

> **the correction** — "There's no reason for Lua to report empty frames, as long as it reports frame numbers."
>
> **the doubt** — "The only reason to write empty frames is for certainty that it didn't accidentally miss any."

The frame number alone makes the still frames visible — the gap between consecutive numbers is the record of the frames that passed with nothing changed. The certainty the empty marker would add is already given by the frame notifier, which fires once per frame and counts the frame before any gate, so a missed frame would be a bug the marker could only detect, never prevent. The marker is written only when something changed.

## Should change detection drop the whole frame when quiet, or only the content?

Reporting every frame appears to contradict a settled principle. The project's own overview says the state channel emits a record only when something meaningful changes, never every frame.

> **the doubt** — "Wasn't there an issue with sending state every frame?"
>
> **the answer** — "The issue was sending the state every frame — roughly 154 bytes. Change detection existed because writing that much on every idle frame was wasteful, and a blocked write inside the frame notifier freezes MAME. An empty heartbeat is five bytes. The objection was about bytes, not about frames."

The principle was never about frames; it was about not rewriting the full state when nothing moved. The heartbeat keeps the spirit — content is still change-gated, only what changed is sent — while the frame number, five bytes on an idle frame, costs next to nothing. Reporting every frame does not resurrect the problem the principle solved.

## Should the reader skip empty frames, or expose every frame?

The wire carries every frame, but the reader sits between it and the consumer, and could hide the empty ones. Whether it does decides whether the consumer can still choose its own step unit.

> **the proposal** — "The reader should report the changes — each change as a new state, every frame numbered — and mark the frames where nothing changed. The consumer decides which changes matter."
>
> **the agreement** — "Right. The reader is a pipe, not a judge: it turns the wire's records into a list of changes, but it never decides a change is uninteresting. The environment drops the unchanged frames; the sandbox keeps them to measure the stillness."

The reader stays uniform for the same reason the sampler does: only the consumer knows which changes it needs. If the reader drops the empties, the sandbox can no longer see the stillness it is measuring.

The decision to expose every empty frame was revisited when the reader's return type was pinned down. A list of `(frame_number, state)` pairs leaves no slot for `None`, so an empty frame had to either repeat the previous state or drop out entirely.

> **the correction** — "I'm fine with dropping empty frames. It doesn't really help to have them."

An empty frame is still visible once it is dropped. The gap between the frame numbers on either side of it is the record that a frame passed with nothing changed, and the sandbox measures stillness by counting that gap. The reader's type stays honest — every entry is a real change.

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
