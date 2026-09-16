# RAM Signals

> ## ⚠️ READ-TIME CRASH WARNING
>
> **Do not read any signal below until the game has booted.** A frame notifier fires on frame 1, when the 6809 has executed almost no instructions and the GIME MMU (mapping the 64 KB CPU space onto 512 KB of physical RAM) is still in its power-on state. `read_u8` through that uninitialized mapping raises a native **SIGSEGV** — a C++ crash, not a Lua error, so `pcall` won't catch it and `print()` output is lost on the way down.
>
> The safe pattern for every read:
>
> 1. Return immediately while `manager.machine.paused` is true.
> 2. Gate on the readiness signal itself — **displayFunction** (`0x02B2–0x02B3`) — and check it **before** touching any other RAM. Only when it is `0xCE66` or `0xD495` (live play — the dungeon or the inventory view) is the rest of the map safe.
> 3. Never sample state first and gate afterward — sampling is itself a read, and doing it before the gate is the crash.
>
> This is why the readiness gate sits *above* the state schema in the frame handler, not below it.

Project-wide catalog of RAM addresses with known behavior. Each entry is headed by the question it answers — signal names and addresses follow.

<br>

<br>

## Names

The game's RAM-map names differ from the schema's field names. The reference docs (`game/ram.md`, `game/code.md`) keep the game's names; the wire schema uses these:

| Game name | Address | Schema field |
|---|---|---|
| perfectMatch | 0x027B | command_parser_matched_exactly |
| foundMatch | 0x0278 | command_parser_matched |
| numWords | 0x0279 | command_parser_word_count |
| whereToPrint | 0x02B7 | where_to_print |
| m0211 (the parse pointer) | 0x0211 | command_parser_position |

`ram.md` also names 0x02F1 `nextToParse`; that is the input buffer itself, not the pointer that ships as `command_parser_position`.

<br>

<br>

## How do I know the game is ready for commands?

**displayFunction** at `0x02B2–0x02B3`. A 16-bit pointer to the game's active screen-drawing routine. This is the primary readiness gate: once it hits `0xCE66` (or `0xD495`), a live-play screen is active and the command area is visible.

Read as big-endian: `byte_at_0x02B2 * 256 + byte_at_0x02B3`.

| Value | Meaning |
|-------|---------|
| 0x0000 | Demo loop — game is playing canned input, screen redrawing is disabled or redirected |
| 0xCE66 | Live play — the dungeon view (LOOK): the normal playing screen (3D view, status bar, command area) |
| 0xD495 | Live play — the inventory view (EXAMINE) |

The transition from 0x0000 happens when the game exits the demo loop, regardless of how that exit is triggered (keyboard priming, clicking the MAME window, or any future automation). It never returns to 0x0000; in live play it moves between `0xCE66` (LOOK, set by `CmdLOOK` at C751) and `0xD495` (EXAMINE, set by `CmdEXAMINE` at D481) as the player switches views.


<br>

<br>

## How do I know a command was matched?

**commandParserWordCount** at `0x0279`. The word-table counter. It resets to 0 between commands, then jumps from 0 to the table size and counts back down to 0 as the parser checks the word table. The 0 → nonzero jump is the matched moment, and it fires on every command.

| Value | Meaning |
|-------|---------|
| 0 | No word decode in progress, or the table is exhausted |
| nonzero | A word decode is running; the value counts the table entries left |

**commandParserMatchedExactly** at `0x027B` also flips to 0xFF on a match, but it stays there. It is cleared and re-set inside one word decode, so its zero usually lasts less than a frame and cannot mark the later matches.

| Value | Meaning |
|-------|---------|
| 0x00 | No exact match yet |
| 0xFF | A complete, valid command matched (stays set) |

Two other signals change with the match and cross-check it:

- **commandParserMatched** (0x0278) = 1 — at least one word matched
- **whereToPrint** (0x02B7) = 255 — the game redirects text output to echo the command

The matched moment is the parser finishing the line, not the effect.

<br>

<br>

## How do I know a command was executed?

**commandParserPosition** at `0x0211–0x0212`. A position in the line the game is parsing: the address of the next character the parser will read. It is two bytes, big-endian, and its resting value is `0x02F1`, the beginning of the line. While you type, it moves forward one letter at a time. When you press Enter, the game reads the command, runs it, and then, at one spot in the game's code, `D2B4`, moves it back to the beginning.

That snap back to `0x02F1` is the executed moment. It happens after every command finishes running, even one that does nothing visible, because the game runs every command to the end and then resets it.

| Value | Meaning |
|-------|---------|
| 0x02F1 | Resting — the game is at the beginning of the line |
| above 0x02F1 | A line is being typed, or a command is running |

One catch: the position also resets when the game rejects a command, or when you press Enter on an empty line. So the reset alone does not tell executed from rejected. Pair it with the rejection text — **command_rejected**, the `???` the game prints instead of running the command. The position back at `0x02F1` and no `???` appeared means the command ran.