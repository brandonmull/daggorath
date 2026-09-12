# Extensibility — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

The environment was built as one fixed thing, shaped around the training pipeline. Work on the sandboxes keeps running into places where it needs to be different — a signal it does not report, a record it does not send, a view it does not offer. This document is about making it shapeable for more than training.

Everything that reads the environment is a consumer. Today there is one, the training pipeline; the sandboxes and the tests that would like to read it are the others this document is about.

## Is the environment generally reusable?

The discussion began as a detail about launching a plugin. The premise behind the discussion was broader than the launch.

> **the premise** — "I think our agent sandboxes should leverage the daggorath_gym module instead of rebuilding everything it does from the ground up. It would be better if daggorath_gym were configurable to allow this."
>
> **the opening question** — "Do we need to modify the gym so that its plugin path is configurable?"
>
> **the answer** — "The environment doesn't need a configurable plugin path. A sandbox that reads raw game state doesn't need the environment's plumbing. It launches MAME itself, like the other sandboxes do, and sets its own plugin path. The environment only ever launches its own plugin."
>
> **the doubt** — "But the plugin path would need to be modified so the sandbox plugins actually run."
>
> **the clarification** — "The plugin path only matters if the environment does the launching. The environment launches only its own plugin, so the path is a sandbox's to set."

The plugin path turned out not to be the obstacle. The real question is what a consumer can take from the environment.

> **the check** — "Are we reusing anything from the gym folder?"
>
> **the tally** — "A sandbox takes almost nothing — the paths, and nothing else. The parts that do real work, the plugin and the schema and the operator, are the very parts a sandbox can't use, because it wants a flag the schema doesn't have and a record for every frame the operator never sends."

The environment is not generally reusable. The environment was shaped for the training pipeline, and any other consumer takes nothing from the environment but the paths.

## Should a consumer reuse the environment's state reporting, or repeat that work for itself?

What a consumer takes from the environment today is the paths and nothing else, which leaves a choice. A consumer can rebuild the environment's reporting for itself, or reuse the environment's reporting as it stands.

> **the wish** — "It would be nice if the gym's reusable pieces were actually reusable, and configurable. Would that just cause too much complexity?"
>
> **the answer** — "The parts a sandbox needs are narrow. It wants the state the environment reports, and how often it reports. Reuse that, and the work is small; the alternative is each sandbox rebuilding the same reporting for itself, which is what happens today."

The narrowness of what a consumer needs is the argument for reuse. Repeating the environment's reporting is not just more work; a rebuild puts a separate copy of the game's reporting in every consumer, and those copies can disagree with one another.

## Should a needed fact permanently extend the environment's state, or be left to each consumer?

Some of the facts a consumer needs are not reported at all.

> **the proposal** — "If there's ever anything we want to add to true game state that we're not currently reporting, we modify the gym to do so. That's fine even if it's only ever necessary for sandboxes and tests."
>
> **the agreement** — "Then the environment is the place for it. A fact about the game is a fact no matter who needs it, and letting each sandbox read memory on its own would scatter that knowledge across every sandbox and let the copies drift from the schema."

A fact a consumer needs joins the environment's state permanently, and later consumers inherit the fact as well. One early wrong turn is worth keeping.

> **the caution** — "Opening the state is one thing; opening all of memory is another. A general way to read anything would be a system to build and keep, and it would let a sandbox reach facts the environment never meant to report."
>
> **the doubt** — "Why do you think logging arbitrary RAM is necessary to get a configurable observation, at least for the current goal?"
>
> **the correction** — "A general way to read memory is not necessary. A fact a sandbox needs is one more field in the state, added when the fact is needed, not a general way to read anything and not something each sandbox builds for itself."

## Should a consumer extend the state, or only narrow the view?

The true state already takes new facts, and the true state's reporting is reused rather than rebuilt. The perceived state is a different kind of thing, and the question is what a consumer can do to it.

> **the extension** — "And if our sandboxes ever need to customize perceived state, we should redesign the gym to allow that."
>
> **the boundary** — "True state and perceived state are different things. Narrowing the view to the facts a lesson cares about is attention, and attention belongs to the agent, so it can live in a wrapper. Changing the gates themselves belongs to the environment, and it would need the view to become a setting."

The boundary drew a line between narrowing and the gates, but the opening move still spoke of customizing the perceived state as if a consumer extended it. That word is the trouble.

> **the refinement** — "Perceived state should be a list of all potential facts a player would actually have access to. The only way consumers should be allowed to modify that list is by reduction — perhaps a simple convention, an inhibitory mask or an array of output fields."
>
> **the choice** — "The keep list is the simplest interface, and it makes clearer to code readers what the output will actually look like."
>
> **the correction** — "A consumer never extends any state. The needs of a consumer can prompt an addition to true state, and in consequence possibly the perceived state, but the consumer never does that on its own."

The consumer never extends. A need prompts the environment to add a fact to true state, and that fact reaches the perceived state only in consequence, when the player genuinely perceives it. The consumer's one operation on the perceived state is reduction, expressed as a keep-list of output fields; the gates themselves stay the environment's.

## Should a consumer receive state synchronously with its command, or asynchronously?

A consumer needs state on its own schedule, independent of the command that produced the state.

> **the proposal** — "We should avoid DaggorathEnv for the causal-timing sandbox and use MameOperator directly, so we aren't hampered by the discrete nature of step() and can issue a command independently of observing frames."
>
> **the agreement** — "That's the right layer. step() sends the command and takes the next record in one call, while a sandbox that wants to watch the frames after a command needs the command and the observation apart. MameOperator keeps send and recv separate already."

So a consumer that wants the command and the observation apart reaches for MameOperator rather than the whole environment, and the environment stays usable by its parts, not only as a whole.

## Open questions

- Whether the recognition flag ships as a state field or as the separate record the events discussion proposes (`events.md`).
- Whether every-frame reporting is a setting on the sampler or a record of its own.
- How the frame a command was posted is pinned, since the operator sends to a socket that the plugin reads on a later frame.
- Whether the gates themselves ever need to become a setting, or stay fixed with reduction as the consumer's only operation.
- Whether the launch belongs in this set at all, or whether consumers keep setting their own plugin path.

## Reference

| Document | What it contains |
|---|---|
| `../2_plans/extensibility.md` | The plan this discussion leads to |
| `events.md` | The deferred event channel and the transient-signal proposal |
| `../3_decisions/state.md` | The state module as it stands |
| `../../../agent/sandbox/causal-timing/README.md` | The experiment that raised the need |
