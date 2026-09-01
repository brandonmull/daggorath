# Deterministic Maze

The game's dungeon is not randomly generated per session. The maze generator
seeds its RNG from a fixed table in ROM, indexed by level, so the maze for a
given level is identical on every boot and every episode.

## Evidence

`MakeMazeLevel` (`CC9C`) seeds the three-byte random generator from a table at
`$CD9F`, offset by the current level:

```
CCA4: 8E CD 9F    LDX  #$CD9F      ; Random number seeds
CCA7: D6 81       LDB  currentLevel ; Offset into seeds...
CCA9: 3A          ABX              ; ...for this level
CCAA: EC 81       LDD  ,X++        ; Copy the 3-byte seed
CCAC: DD 6B       STD  rndSeedA    ; ...into the
CCAE: A6 84       LDA  ,X          ; ...current
CCB0: 97 6D       STA  rndSeedC    ; ...seed
```

`$CD9F` is cartridge ROM — read-only. The seed bytes (`rndSeedA`/`rndSeedB`/
`rndSeedC`, RAM addresses `0x006B`–`0x006D`) are written only here, never from a
timer or any value that differs across boots.

## Mechanism

`SWI_7` (`C4CF`) is the game's random-number routine — a three-byte
linear-feedback shift register over `rndSeedA`/`rndSeedB`/`rndSeedC`. Given the
same seed, it produces the same sequence every time.

## Consequence

The environment presents the same maze every episode. This is the game's
design, not a defect, so the environment works with it rather than varying it.
