# C++ Port

_Replacing the MAME backend with a faithful C++ port of the original game._

## Rationale

The project's value is producing a trainable environment, not the
reverse-engineering. MAME and the RAM archaeology were the expensive means the
black box forced, not the point. A faithful C++ port is a simpler path to the
same value.

## Candidates

- `gondur/dungeons-of-daggorath` — the Linux port v0.5.1 of Richard Hunerlach's
  Windows C port. C++ source, `src/` present. Not a reimplementation: the
  original 6809 assembly translated line-for-line, so the hard mechanics
  (heartbeat combat, darkness, sound-before-sight, 154 commands, long descent)
  are the real mechanics.
- `MichaelSpencerJr/DungeonsOfDaggorath` — the original 6809 `.ASM` source, with
  `grant_of_license.png` checked in alongside it. The license is Douglas Morgan's
  grant.

## What survives the swap

The observation design, the factored action space, fact-vs-valuation, the reward
wrapper, the trainer.

## What disappears

MAME, the Lua plugin, the FIFO/TCP bridge, the RAM archaeology, the firmware, the
ROMs — and with them the setup and legal friction around the CoCo 3 firmware.


## Next

Start a `cpp-port` branch and map `gondur/dungeons-of-daggorath`'s `src/` before
writing any integration code.
