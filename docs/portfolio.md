# Portfolio

_Why the root README reads the way it does, and the value claim behind it._

## The spine: a world that didn't exist

*Dungeons of Daggorath* did not exist as a world a machine could enter, and now
it does. The accomplishment is a contribution, not a hardship — what the project
gave, not what it endured. The difficulty is real, and it comes second, as the
challenges along the way.

Two things were given.

**A world.** The game is now a live environment with defined observation and
action spaces, so a training loop can be pointed at it. Knowledge was never the
missing piece: the author released his source, and the community mapped much of
the memory. What did not exist was anything that could *run*. The contribution
is the distance between documentation and a running system — a spec is not an
integration.

**An interface worth building on.** Getting an agent to play once is a demo;
whether anyone else can use the result is a design question. The interface was
built against what a person training an agent actually needs, and the
key choice is that the environment holds no opinion about what the
agent should want — it reports what is true and returns reward `0.0`, so the
objective belongs to whoever is training. That is fact-vs-valuation restated as
a service to the developer.

## Why this world is worth having

A new environment on its own invites a shrug. The value is in this one's
properties. The game keeps no score at all; the dungeon is dark until a torch is
lit, and what cannot be seen is heard; every action is one of 154 command phrases; nothing pays off quickly. Those are sparse reward, partial
observability, a large compositional action space, and a long horizon — the four
conditions modern RL handles worst, and testbeds posing them are scarce. The
game's age stops being a curiosity and becomes the reason it is useful.

## The README's shape: a dungeon entrance

The README is a journey, not a table of contents. A reader arrives, reads a
sign, surveys a camp, and steps inside. Section titles draw on the game's own
mechanics — the torch, the gate, the unmapped depths — rather than wearing the
theme as decoration.

**The status is a sign.** Honesty-before-aspiration lives in the carving above
the entrance: "To all who would enter: the gate stands open, but the depths are
still unmapped." The environment runs (the gate is open); no agent has beaten
it and no curriculum exists (the depths are unmapped). What is unfinished is
worldbuilding, not a caveat.

**The four stops are decisions, not doors.** "Outside the entrance" is a camp:
step inside, read the stone, train at the fire, forge your torch. Each names a
different means of engagement, and each is honest about its kind — step and
forge are things you do, the stone is a thing you read, the fire is a thing you
train at. A door can lead to a reading room; forcing every stop to be an action
would misrepresent what it actually is.

**The deep dive is the inside.** "What the dark hides" holds the argument. The
spatial logic runs above → outside → inside: read the sign, survey the camp,
step through, and learn what the dark was hiding.

Two details are load-bearing and easy to lose in a rewrite. The sign says "the
gate," singular — the camp has one door, and "Step inside" is that door; a
plural would break the count. And the forge is its own stop, not a sub-point of
training, because it names the craftsman's contribution — bring your own torch,
build on it — as something special rather than a footnote.

## The README opening — binding rules

Five rules govern the opening, each earned by a draft that violated it:

1. **Claim the platform, not the player.** "Software can play it now" is the
   weaker claim — an unfinished outcome, and one a scripted bot could make
   without any of this work. What exists is an environment.
2. **Credit what came before.** The author's published source and the
   community's memory map are the foundation this project stands on. Any phrasing that implies
   the game was sealed or undocumented is false and gets cut.
3. **State the idea and stop.** Supporting facts belong to the section that owns
   them. If a fact appears under "What the dark hides," it does not
   appear in the opening.
4. **No jargon before value.** MAME, the 6809, Lua, Gymnasium, and `Env` do not
   appear in the opening. They belong in Step inside and the rest of the camp.
5. **No insider references.** `PPO(...)`, `gym.make("CartPole-v1")`, and "this
   project is the `make`" only land if the reader already knows the toolchain.
   Translated to plain terms: normally you download a ready-made world; there
   was none to download.
