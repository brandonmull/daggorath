# Extensibility

_See [overview.md](../../../docs/overview.md) for project context and architecture._

This plan specs the changes that make the environment reusable by consumers beyond the training pipeline, answering the five questions in `../1_discussions/extensibility.md` in the same order. The changes are three: eight new facts join the true state permanently, the sampler can report every frame rather than only on change, and a consumer narrows the perceived view by reduction. What a consumer never does is extend — that stays the environment's, prompted by a consumer's need.

## Is the environment generally reusable?

The environment becomes reusable by being usable by its parts, not only as a whole. A consumer — anything that reads the environment: the trainer today, and the sandboxes and tests that want to — takes the state reporting directly, rather than the paths alone. Reusability is not a surface of its own; it is what the three changes below add up to.

## Should a consumer reuse the environment's state reporting, or repeat that work for itself?

A consumer reuses the environment's state reporting rather than rebuilding it. The reusable surface is the wire schema — `FIELDS` in Python, `SCHEMA` in Lua — the sampler in `state.lua`, and the operator, `MameOperator`. Repeating the reporting puts a second copy of the game's facts in each consumer, and the copies drift.

A consumer sets two things about the reporting: which facts it reads — the schema, extended in the next section — and how often it receives them. How often is a setting on the sampler, not a record of its own. The setting is `report_every_frame`, a boolean defaulting to false, which is today's change-gated behavior. When true, the sampler writes the numeric frame record (`S`, or `T`/`B` when the text also changed) on every sampled frame whether or not the frame differs from the last one; the world channels (`M`, `C`, `O`, `H`) keep their own change gate. With it on, `recv()` returns a state every frame.

The setting travels the same path the IPC configuration already does:

```
the operator's launch
    → writes the every-frame choice into the emulator process environment
    → the plugin entry reads the choice and hands it to the sampler
    → the sampler drops the change gate for the frame record
```

The default leaves the trainer's behavior unchanged.

## Should a needed fact permanently extend the environment's state, or be left to each consumer?

A fact a consumer needs joins the environment's state permanently; no consumer reads it from memory for itself. This plan adds eight facts, prompted by the causal-timing sandbox's need to see when a command is matched and when an object moves between the hands and the pack. They join the schema in their category, not appended to the end; the frame grows from 23 to 35 bytes and the schema from 19 to 27 entries.

The schema is listed categorically — mode, parser, position, light, torch, holdings, body, heart, wizard — and each group gains a comment above it in `FIELDS` and `SCHEMA` naming its category, so the ordering reads at a glance and a later addition lands in its category. Two existing fields move to make the categories contiguous: `display_function` joins `game_mode` under mode, and `player_fainting` joins the body group. The wire is a single shared contract, so the offsets shift with the reorder and both sides move together.

The eight facts file into two of those categories: the recognition flag and its companions under parser, the pointers under holdings. The first four are the fingerprint the parser leaves when it consumes a command; the last four are the game's pointers into the object array for what the player holds and for the head of the pack:

| Field | Category | Lua | Address | Width |
|---|---|---|---|---|
| `perfect_match` | parser | `perfectMatch` | 0x027B | 1 byte |
| `found_match` | parser | `foundMatch` | 0x0278 | 1 byte |
| `num_words` | parser | `numWords` | 0x0279 | 1 byte |
| `where_to_print` | parser | `whereToPrint` | 0x02B7 | 1 byte |
| `left_hand` | holdings | `leftHand` | 0x021D:021E | 2 bytes |
| `right_hand` | holdings | `rightHand` | 0x021F:0220 | 2 bytes |
| `torch_ptr` | holdings | `torchPtr` | 0x0224:0225 | 2 bytes |
| `first_pack_object` | holdings | `firstPackObject` | 0x0229:022A | 2 bytes |

The pointers are sixteen-bit and follow the existing wire convention — big-endian in RAM, little-endian on the wire. The recognition flag and its companions are transient, flipping and resetting within a few frames, so they are observable only with the every-frame reporting of the previous section.

## Should a consumer extend the state, or only narrow the view?

The consumer never extends. A need prompts the environment to add a fact to true state — the previous section — and that fact reaches the perceived state only in consequence, when the player genuinely perceives it. The consumer's one operation on the perceived state is reduction.

The perceived state is the complete list of facts the player has access to: the nineteen scalar facts plus the five world channels — `hands`, `pack`, `creatures`, `objects`, `map`. `as_perceived()` returns that whole list by default. The eight new facts are not in it: parser internals and RAM pointers are not things the player perceives, so no reduction can reach them and no consumer can put them in the view. They live only in true state, read through `current_state`.

A consumer narrows the view with a keep-list — an array of output-field names (`keep_fields`) to retain, scalar facts or whole channels, everything unnamed dropped:

```
as_perceived
    → returns the full perceived state when no keep-list is given
    → otherwise keeps only the named scalar facts and channels
    → drops everything unnamed
    → returns an observation space matching the kept fields
```

The default, no keep-list, is the full perceived state. The reduced observation's `Dict` space derives from the same keep-list, so the space always matches the output a consumer gets.

Whether the gates themselves — the light, mode, and line-of-sight filters that shape the world channels — ever need to become a setting is left open; this plan changes no gate.

## Should a consumer receive state synchronously with its command, or asynchronously?

A consumer that needs state on its own schedule, independent of the command that produced it, uses `MameOperator` directly — `send` and `recv` are already separate there. `DaggorathEnv.step()` keeps its pairing of a send with a receive; a consumer that wants the two apart reaches beneath the environment to the operator, and the environment stays usable by its parts. Consumers that launch MAME themselves keep setting their own plugin path; that is not part of this plan.

## Reference Documents

| Document | What it contains |
|---|---|
| `../1_discussions/extensibility.md` | The discussion this plan answers |
| `../findings/ram-signals.md` | The recognition flag and its companions |
| `objects.md` | The holdings pointers and the object array |
| `../3_decisions/state.md` | The state module and wire format as it stands |
| `../../../agent/sandbox/causal-timing/README.md` | The consumer whose need prompts the new facts |

