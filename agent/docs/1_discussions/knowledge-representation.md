# Knowledge Representation

_How the agent holds two kinds of knowledge — experience and cause — and how it uses them together to reason. This is an open discussion, not a plan. It follows [`knowledge-and-reasoning.md`](knowledge-and-reasoning.md), which argues why knowledge should live outside the weights; this doc describes the shape that knowledge takes, and the parts still undecided. It keeps the exchanges that produced it, not just the conclusions._

## What are the two kinds of knowledge?

The framing that started this discussion came first:

> **the premise** — "Each step executes an action against a given game state and returns a resulting state. If we capture those transitions over a session, we could consider memory of them experiential knowledge. My intention is to later pair this with a secondary set of data representing the agent's causal knowledge — to iterate over both in conjunction, and generate predictions as a means of reasoning."
>
> **the answer** — "The point of holding both is to read them together: place the situation the agent faces against the distilled causes, let the remembered moments confirm or contradict them, and predict what an action will do before committing to it. That pairing is what this project means by reasoning."

The agent ends up with two sets of knowledge, and they are different things:

- **Experience** is the record of what happened. Each entry is one moment: where things stood, what the agent did, and what changed as a result.
- **Causal knowledge** is the summary of what causes what, drawn from many moments. Experience says "in this situation, pulling put the torch in my hand." Causal knowledge says "pulling moves the torch from the pack to the hand."

Experience by itself is just a recording. Causal knowledge by itself is a claim with nothing behind it. The representation holds both side by side so the agent can compare the situation it faces with what it has learned causes what, and let the recorded moments confirm or contradict that. Predicting before acting — that is what this project calls **reasoning**.

This is the same split `knowledge-and-reasoning.md` draws between **memory** (true for one run) and **knowledge** (true across runs). Experience is the accumulated moments; causal knowledge is the summary; and consolidation is the step that turns one into the other.

## What does experience look like?

![Experiential knowledge representation](knowledge-representation-experiential.jpg)

The request came in with the figure still taking shape, wanting the idea pushed further than the drawing carried it. It was hard to tell what had landed and what had not. The reply found the cause: three separate layers pressed into one view, which is what makes it confusing.

> **the request** — "Please have a look at this image and tell me what you think. It needs to be completed. There are implied rules and mechanics not made explicit yet. The overall concept needs a better introduction, considerate to a wide variety of readers."
>
> **the diagnosis** — "The figure puts three different things on one canvas and never says which is which — data, process, and judgment. A reader sees a box, an arrow, and three colored pills, and cannot tell that the pills answer three unrelated questions."

Pulled apart, the three layers are:

| Layer | What it is | In the figure |
|---|---|---|
| Representation | the data: situations, actions, effects, masks and values | the boxes and arrows |
| Capture | how the data gets made: runs, lessons, waiting for the game to settle, how the next action is chosen | the ellipses and the "divide the lesson here" rule |
| Valuation | the agent's judgment: causal or not, progress or setback, reward or penalty | the pills |

They describe the same object but answer different questions. The `causal` / `non-causal` label, for example, is a field on an arrow (data), but its value is decided during capture.

That overload had an obvious remedy:

> **the proposal** — "Each layer wants its own figure — three views of the same graph, not one overloaded diagram."
>
> **the agreement** — "We should probably create a different figure for each layer, yes?"

The first of the three is the data itself. A run of play looks like a graph. Each node is one situation the agent saw. Each arrow is an action taken from that node, along with what changed. Over a run the arrows trace the path the agent walked, and where more than one action was possible, the path branches.

The extent of that graph was settled early:

> **the definition** — "One session, in my mind, is from the start of the game to victory or death. In the graph, that's from the initial node to the terminal node."

The basic unit has three parts:

- the **situation** (also called the precondition) — what the agent sees before acting;
- the **action** — one command;
- the **effect** — what changed: which facts are different afterward, and how.

An effect is not something to detect on its own. It is simply the difference between two situations — and that difference has two parts: a **mask** that says *which* facts changed, and a **value** that says *how* they changed (up or down, by how much). Causal knowledge stores the mask; the value keeps the detail.

A situation is not the whole picture either. Only some facts define it — the ones that matter for recognizing it again ("a torch in the pack" versus "a torch in the hand"). That smaller set is the situation's own mask.

An action leaves behind a fact, and it took an exchange to see that there are two kinds:

> **the claim** — "There are two kinds of fluent that an edge can write — `known` (EXAMINE writes what the agent has seen) versus game facts (PULL and USE write the torch's location and light). They compose differently: action links compose by a shared variable, while perception links compose only through reasoning."
>
> **the confusion** — "I'm not sure what you mean."
>
> **the explanation** — "An action leaves a fact behind, and there are two kinds. A *world fact* is something that changed in the game — pulling the torch moves it from the pack to the hand — written by actions like PULL and USE. Those connect directly: one action writes the fact, and the next reads it. A *knowledge fact* is something the agent now knows — that the pack holds a torch — written by actions that reveal, like EXAMINE, or by sight. Those do not connect directly; they connect through reasoning, because the agent acts on what it has learned."

In the figure, the `known` label marks the second kind.

## Which facts should a lesson watch?

The full picture is noisy. The heart beats, the torch burns down, tiredness climbs, and most of that has nothing to do with the lesson being learned. So a lesson names the facts it cares about, and every other fact is dropped before two situations are compared. The comparison then reports only what the lesson watches.

The reasoning was stated plainly:

> **the reduction** — "I think the perceived state needs to be reduced, per lesson, to avoid noise and allow quicker development of causal knowledge. Constraining perception this way is effectively the same as giving the model attention. For my immediate purposes I will hand-pick the parameters, but I believe the technique can be automated."
>
> **the consequence** — "One consequence of doing things this way is that we will have to conceive a solution for combining knowledge from lessons, such that the resulting knowledge is in terms of the full field set."

The combination is not simple, because a lesson ignores some facts on purpose, and an ignored fact may have been hiding a real influence. So the pieces must be combined carefully, and the result must stay open to revision. (`knowledge-and-reasoning.md` leaves the same problem open, under "unifying overlapping masks.")

## When is one step finished?

Each step is a situation, an action, and the effect of that action. For the effect to mean anything, it has to belong to the action that caused it — so before any of this can work, one question has to be answered: **what counts as one step?** A command has three separate moments, and they are easy to confuse:

- **matched** — the game's parser recognizes the command;
- **executed** — the command's code runs;
- **changed** — the game state actually differs because of it.

Only the first leaves a mark we can read.

The exchange that produced this is worth keeping:

> **the discovery** — "Whoa — I didn't realize we were stepping until settled. I was wondering why checkpoints capture so many steps. It doesn't seem right to me."
>
> **the finding** — "Reading the code showed the opposite: the `step()` call sends a command and takes the very next record, and the wait-for-settle is an unimplemented follow-up. The many steps come from change-gating — every frame the state differs produces a record, and the heart, the torch timer, and tiredness differ often."
>
> **the insight** — "Nothing in memory says the handler ran, and nothing says the change was caused by the command. That last one has no sensor at all — it is the very inference the agent is supposed to make, so a ready-made signal would give the answer away."
>
> **the doubt** — "We need a signal that tells us the moment a command has been executed and the state has changed because of it. I don't know if `perfectMatch` is such a signal. The `command_text` echo seems more probable, assuming the command doesn't execute before the whole line has gone through the window. I think we have to sandbox this and try a variety of commands, not just the torch — the only reason a human can tell so easily is prior world knowledge and reasonable expectation."
>
> **the proposal** — "What if we decouple the action from the effect and let the agent pause further actions while it waits for a 'reasonable' effect? I can see where we'd want to record several state changes inside an allotted time slot, and block further actions at least while the agent's confidence about causation is low."
>
> **the synthesis** — "The world never goes fully quiet, so the window can't wait for the whole state to stop changing. But the lesson's own reduced facts can. Close the window once those facts hold still for a few frames — the reduction then does double duty: it quiets the noise and says when to stop waiting."

So the approach is to **separate the action from its effect and wait out a window**: issue one action, block further actions, watch what changes during the window, then close it and record the effect. While the agent is unsure whether a cause is real, the window can stay open longer; as its confidence grows, it can shorten. A window that changes length makes the reward's time discount harder to reason about, so a fixed-length window is simpler.

The sandbox at [`../../sandbox/command-latency/`](../../sandbox/command-latency/README.md) is measuring these three moments. This doc lays out the question; the sandbox is where the answer comes from.

The three moments and the no-action control are the two halves of one need — causal attribution — named in [`causal-attribution.md`](causal-attribution.md).

## How do experience and causal knowledge meet?

The two datasets are used together in two passes, at two different times:

- **Consolidation** happens offline. It reads the accumulated experience and distills the clean cause-and-effect claims from it.
- **Execution** happens live. It matches the situation at hand against those claims, then picks an action.

The match does not have to be exact. A loose match, weighted by how well the remembered moments turned out, lets the agent choose probabilistically rather than all-or-nothing. The full bridge is not buildable yet — the causal side is still being worked out — but the experience side can be built ready for it. It needs to record the reduced situation, the action, the effect (mask and value), and how the outcome was judged. Those are exactly what consolidation will sort through and what execution will match against.

## Vocabulary

- **Situation (precondition)** — what the agent sees before acting. Never the game's hidden truth.
- **Action** — one command.
- **Effect** — the difference between the situation before an action and the situation after it.
- **Transition** — a situation, an action, and an effect, recorded as one unit.
- **Session** — one playthrough of the game, from the start to the end (a win or a death).
- **Lesson** — one unit of the curriculum: a single goal and a single reduced set of facts.
- **Causal edge** — a transition generalized from many instances: this action, from this kind of situation, produces this kind of effect.

## Open questions

- **The settle signal.** Is there a reliable signal that a command has finished, or should the window be defined by the lesson's own facts going quiet? The sandbox is measuring this.
- **Combining lessons.** How should the knowledge from different lessons be combined into one full picture without dragging in each lesson's blind spots?
- **The no-action control.** The world changes on its own. How is that background change captured, and what about the facts the agent does control?
- **False causation.** A link may be labeled causal and later turn out wrong. How is that caught and corrected, across sessions?
- **The bridge.** What exactly does execution match on, and how does a loose match weigh a cause by how it turned out before?
- **Confidence.** How is confidence in a cause measured (how often seen, how consistent?), and should it control the window's length?

## Reference

| Document | What it contains |
|---|---|
| [`knowledge-and-reasoning.md`](knowledge-and-reasoning.md) | The theory — why knowledge lives outside the weights |
| [`curriculum.md`](curriculum.md) | The lesson ordering and the per-lesson rewards the valuation layer feeds |
| [`../../sandbox/command-latency/`](../../sandbox/command-latency/README.md) | The experiment measuring the three moments |
| [`../../sandbox/causal-diff/`](../../sandbox/causal-diff/README.md) | The probe computing the effect diff |
