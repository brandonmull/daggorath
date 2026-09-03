# Screen Reading

_1 Sep 2026_

## Decision

The command area's 1024 pixel bytes (4 text rows × 32 characters × 8 scanlines) are captured each frame and decoded back to text in Python by reversing the game's own `PrintRegChar` drawing arithmetic against a fixed 32-character font.

## Why

- **No OCR.** The game draws every letter from a fixed 32-character font table, so the decoder reverses that exact arithmetic — decompress 5 packed bits into 7 rows, un-shift, un-XOR with `comColor` — rather than recognizing pixels.
- **The font lives once, in Python.** Lua only moves bytes; the font table and the decode math exist in a single place so the two sides cannot drift.

## What Changed

- `daggorath_gym/screen.py` — `FONT_PATTERNS`, `decode_character`, `decode_text_row`, `decode_command_area`.
- `emulation/plugins/daggorath/state.lua` — the `T`/`B` pixel records feed the decoder.

## Reference

- Sandbox: `gym/sandbox/screen-reading/` — validated capture + decode pipeline
- Disassembly: `docs/references/game/code.md` — `PrintRegChar` and the font table
