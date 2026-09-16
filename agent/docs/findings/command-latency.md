# Command Latency

The torch experiment recorded three fresh boots of two commands, and the fighting experiment recorded three loads of a saved encounter. Read together, they show the matched signal is `command_parser_word_count` (not `command_parser_matched_exactly`), the effect lands one frame after the match for the torch and about 19 frames for combat, and the long wait before a match is typing, not processing.

## The matched signal is `command_parser_word_count`, not `command_parser_matched_exactly`

`command_parser_matched_exactly` (0x027B) was documented as the primary matched signal, but it stays set. In the fighting trace it turns to 0xFF on the first match and never returns to 0, so a check for the jump from 0 to 0xFF misses every later match.

The disassembly explains why. In `DecodeInput` (CBEC), `command_parser_matched_exactly` is cleared at CBF6 and set to 0xFF at CC15 when the exact match is found, both inside one word decode. For a word that matches early in its table, the clear and the set happen within a single frame, so the zero never lasts long enough for the sampler to see it. `command_parser_word_count` (0x0279) is the table counter: it is loaded with the table size at CBFA, then counted down once per table entry at CC23. Large tables make that loop take several frames, so the moment `command_parser_word_count` jumps from 0 to a nonzero value can be seen on every word decode.

Watching for that `command_parser_word_count` jump gives clean matched offsets for every command in both traces.

## The wait before the match is typing

PULL is 15 characters and matched 157 frames after the post; USE is 8 and matched 83; ATTACK LEFT is 11 and matched 111; ATTACK RIGHT is 12 and matched 120. All four work out to about ten frames per character, the plugin typing the phrase in. A step's latency is mostly typing: roughly ten frames per character, then the handler's own frames.

## The handler runs in about one frame

For the torch, both commands changed the field being watched one frame after the match. PULL moved the torch from pack to hand; USE lit it.

| Post (frame) | Command | Echo begins | Matched | Executed |
|---|---|---|---|---|
| 1177 | `PULL LEFT TORCH` | +8 | +157 | +158 |
| 2011 | `USE LEFT` | +8 | +83 | +85 |

## Combat resolves over about 19 frames

For the fighting child, the empty left hand hit the spider first: matched +111, changed +130. The sword in the right hand killed it: matched +120, changed +139. Both effects landed 19 frames after their match, where the torch's landed 1. Combat resolves over more frames than inventory commands.

Empty hand and sword show the same 19-frame gap between match and effect against this spider. The only difference between the two hands is phrase length, which shifts the matched arrival by one character's typing time.

## Matched is not changed

After the kill, every later attack matched and changed nothing. That is the proof that a command can match without changing anything, which is what the control was for.

## `m0221` marks a weapon swing, and recovers

`m0221` tracks how exerted the player is, and it does three things. A landed creature hit raises it. It falls as the heart recovers. And every weapon swing raises it by the swing's cost, added in `CmdATTACK` at D2D8 before the game decides whether the swing hit, so a missed sword attack still costs exertion.

The fighting trace shows the swing cost exactly. Every `ATTACK RIGHT` (sword) raises `m0221` by 2, then it falls back to 0 over about 200 frames. The empty-hand `ATTACK LEFT` costs nothing, so its swings leave `m0221` unchanged.

So `m0221` is not a clean hit signal, because recovery and creature hits share it. But for a weapon attack it is a clean execution signal: the swing's cost marks the handler running, hit or miss.

## `command_parser_position` marks when a command has finished

The executed signal the sandbox was missing is `command_parser_position` (0x0211), the game's cursor into the command being typed. It snaps back to 0x02F1 once a command has run, on every command, even one that does nothing visible; paired with `command_rejected` (the `???` echo) it separates executed from rejected. The full field entry is in [`../../../gym/docs/findings/ram-signals.md`](../../../gym/docs/findings/ram-signals.md). It is not on the wire yet.

## The echo never clears

The command echo stays in the command area as scrollback, so the echo clearing cannot mark when processing completes. The written moment is the echo beginning, the first character the game draws.

## A saved state replays identically

The fighting child's three sessions replayed identically from the same saved state, so a saved state measures offsets, not variance.

## What the combat numbers cover

The 19-frame combat resolution and the empty-hand-versus-sword equality were measured on one state: starting strength 160, weight 35, wooden sword, empty left hand, no flask effect, against a spider. They are established for that state, not for the game. Enemy type, weight, strength, flasks, and other weapons are all unmeasured variables that could move the number.

## The trace outlives the reading

The first torch reading reported USE matching six frames after the post, a stale flag read as a fresh moment. The correction came from reading the same traces again. The fighting matched readings came the same way, by switching the code that looks for a match to `command_parser_word_count` and re-reading the traces already on disk.

## Reference

| Document | What it contains |
|---|---|
| [`../../sandbox/command-latency/README.md`](../../sandbox/command-latency/README.md) | The sandbox these readings come from |
| [`../1_discussions/command-abbreviation.md`](../1_discussions/command-abbreviation.md) | The delivery follow-up these readings opened |
| [`../../../gym/docs/2_plans/command-consumption.md`](../../../gym/docs/2_plans/command-consumption.md) | The matched-signal plan this corrects |
| [`../../../gym/docs/2_plans/combat-detection.md`](../../../gym/docs/2_plans/combat-detection.md) | The combat fields the fighting child watches |
| [`../../../docs/game/combat-model.md`](../../../docs/game/combat-model.md) | The strength-vs-damage model and the attack path |
