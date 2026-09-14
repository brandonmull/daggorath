# Command Latency

The torch experiment recorded three fresh boots of the same two commands — PULL LEFT TORCH, then USE LEFT — and read the traces afterward. Processing starts on the parser's match edge; the effect lands one frame later; and the long wait before the match is the command being typed, not the game working.

## Processing starts on the match edge, not the match level

`perfect_match` latches. It flips to `0xFF` when the parser matches a line and stays there until the parser re-arms for the next one — dropping to 0 for a single frame just before the following match. Reading the level treats a stale flag as a fresh moment; the moment is the 0 → `0xFF` edge. Across the three boots the edge landed on the same frame, one frame before the effect.

## The handler runs in about one frame

Both commands changed the watched field exactly one frame after the match, in every session. PULL moved the torch from pack to hand; USE lit it. At the resolution the sampler can see, the gap between processing starting and the effect landing is one frame. `where_to_print` pulses to 255 on that same frame, a co-signal for the effect.

| Post (frame) | Command | Echo begins | Matched | Executed |
|---|---|---|---|---|
| 1177 | `PULL LEFT TORCH` | +8 | +157 | +158 |
| 2011 | `USE LEFT` | +8 | +84 | +85 |

## The wait before the match is typing, not processing

PULL is 15 characters and matched 157 frames after the post; USE is 8 characters and matched 84. Both work out to about 9.7 frames per character — the plugin's keyboard typing the phrase in, not the game thinking. The game's own cost is the single frame after the match. A step's latency is therefore dominated by delivery: roughly ten frames per character of the phrase, plus one.

## The echo never clears

The command echo stays in the command area as scrollback, so "the echo clearing" cannot mark processing complete. The written moment is the echo beginning — the first character the game draws, eight frames after the post, the same gap for both commands.

## The trace outlives the reading

The first reading reported USE matching six frames after the post: a latched flag read as a level. The correction came from reading the same traces again — no boot was repeated. Deciding nothing during the run is what made the fix cheap; it is also why the three traces matching byte-for-byte counts as a result.

## Reference

| Document | What it contains |
|---|---|
| [`../../sandbox/command-latency/README.md`](../../sandbox/command-latency/README.md) | The sandbox these readings come from |
