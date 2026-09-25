# Objects

Reverse-engineered from the 6809 disassembly ([`code.md`](../../gym/docs/references/game/code.md)) and the RAM map ([`ram.md`](../../gym/docs/references/game/ram.md)). The object classes, their proper names, and the states each can occupy. The environment's sampling and wire format are in [`gym/docs/2_plans/objects.md`](../../gym/docs/2_plans/objects.md); the command grammar that names them is in [`commands.md`](commands.md).

## Classes and proper names

Six classes, each with its proper names. The full specifier table and proper-name tokens are `commands.md` Appendix D.

| class | proper names |
|---|---|
| TORCH | PINE, LUNAR, SOLAR, DEAD |
| SWORD | ELVISH, IRON, WOODEN |
| SHIELD | BRONZE, LEATHER, MITHRIL |
| FLASK | ABYE, HALE, THEWS, EMPTY |
| SCROLL | SEER, VISION |
| RING | ENERGY, FINAL, FIRE, GOLD, ICE, JOULE, RIME, SUPREME, VULCAN |

## The states

### Reveal — every object

An object acts as its base class until revealed. Unrevealed, the player sees only the class ("TORCH"); revealed, the player sees the proper name ("PINE TORCH"). Reveal is strength-gated: `CmdREVEAL` requires `pStrength >= strength_to_reveal × 25`. The reveal threshold is the object's slot + 11, cleared to 0 once revealed. The 3D view draws floor objects as pictures keyed by class alone (`D9EE`), so an object on the floor is seen only as its class until it is picked up and revealed.

### Lit — torch, a flag

The lit torch is the one `torchPtr` (0x0224) points at, so there is at most one lit torch. `CmdUSE` on a torch sets the pointer and stows the torch (D74C–D74E); `CmdPULL` on the lit torch clears the pointer, extinguishing it (D5B1–D5B5). The lit torch is highlighted in the EXAMINE display (D4F1–D4F5). This is the one state that is a flag rather than a rename.

### Burn — torch, true-state with a rename

The lit torch's minutes (slot + 6) decrement once a minute (`T3_TimeTorch`, D19B); its physical and magic light (slots + 7, + 8) track the remaining minutes, so the dungeon dims as it burns. Once the minutes fall to five or below, the torch renames to DEAD (proper 0x18) and is revealed (D1A6–D1AE). The timer and light are true-state; the player perceives the burn only as the dimming and the DEAD rename.

### Used — flask, a rename

THEWS, HALE, and ABYE each pour an effect once, then the flask renames to EMPTY (proper 0x17) and is revealed (D792–D796). No reveal is needed before drinking; the drink is the reveal.

### Incanted — ring, a rename

Each ring carries a hidden incantation word (slot + 7). `CmdINCANT` matches a typed word against it and, on a hit, writes the word into the ring's proper-name field (slot + 9), transforming it (D5D8–D5E9). Powered rings carry strikes (slot + 6); each attack decrements the count, and at zero the ring degrades to GOLD (D2E2–D2F4).

## Summary

| class | states beyond reveal |
|---|---|
| TORCH | lit (flag), burn (true-state + DEAD rename) |
| SWORD | none |
| SHIELD | none |
| FLASK | used (EMPTY rename) |
| SCROLL | none |
| RING | incanted (rename) |

Every state except the torch's lit is a rename, carried by the proper name. The torch's burn level stays true-state, perceived only as dimming light.
