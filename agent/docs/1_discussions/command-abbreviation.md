# Command Abbreviation

_The wait before a command is matched is the phrase being typed, not the game working — about 9.7 frames per character, with no rate to tune. Abbreviating the posted phrase cuts that wait three to four times over. Open discussion; it follows the first measurement in [`../findings/command-latency.md`](../findings/command-latency.md), and asks what the short form is, what makes it dangerous, and what has to be checked before it ships._

## What is the wait actually paying for?

The proposal came with a reason attached, and the reason named the wrong payer.

> **the proposal** — "Now that we've determined long command phrases cause a huge lag in command latency, we should probably opt for utilizing abbreviated commands versus full words."
>
> **the correction** — "The lag is real, but it isn't the game thinking. The phrase is being typed in, character by character, at about 9.7 frames each — and MAME's options expose only whether the natural keyboard is used, not how fast it types."

The measurement puts `PULL LEFT TORCH`, fifteen characters, 157 frames from the post to the match; `USE LEFT`, eight characters, 84. The game's own work is the single frame after the match, so what a step pays for is the length of the phrase. That makes the phrase's rendering the lever, and the typing rate something to route around rather than tune.

## What can stand in place of the full word?

The manual answers this before any experiment has to.

> **the answer** — "The game accepts abbreviations — the shortest set of letters that cannot be confused with another command — and it still requires the spaces between the words."

`PULL LEFT TORCH` becomes `P L T` and `USE LEFT` becomes `U L`: five keys and a return instead of fifteen, two instead of eight. The wait shrinks with the character count, and the same command is matched at the end of it.

## What is the short form — the command or its rendering?

Shorter text is easy to mistake for a shorter command.

> **the distinction** — "The phrase is the command's identity; the posted text is a rendering. The agent chooses an index either way, so shortening changes only what the plugin types."

Nothing in the command enumeration or the action space moves. The change lives where a phrase becomes keystrokes, and every index keeps its meaning.

## What makes a short form dangerous?

The failure is rejection, not delay, and it is already priced.

> **the doubt** — "An abbreviation that is too short prints `???` and never sets the match flag — and our reward prices rejection. A bad abbreviation isn't a slow step; it's a wrong one."
>
> **the caution** — "The manual's list is partial: it does not carry `PULL LEFT TORCH` at all, and it names a ring our ROM's table does not contain. The manual is a guide; the parser is the authority."

The rejection penalty turns a delivery detail into a correctness risk, so the short forms cannot be derived by eye. They have to come from the game's own tables and then be proven by the game's own answer.

## What does shortening leave unchanged?

This is a delivery change, not a new measurement.

> **the limit** — "Shortening moves the wait before the match. It does not move the frame after it, so the finding stands: the effect still lands one frame after the command is matched."

The experiment has nothing to re-run. What changes is the real-time cost every step carries, which is what the step unit is being chosen to fit.

## What has to be checked before the short form ships?

The forms need computing and then proving, in that order.

> **the proposal** — "Compute the shortest unambiguous prefix from the tables we already hold — first-word, second-word, class, proper-name — so there is no second list to drift, then issue each candidate and watch for the rejection."

A derivation alone is a claim about the parser's tables; only the parser can confirm it. A validation run of the shape this sandbox already runs — a schedule of posts, the watched signals read afterward — settles it, and can check at the same time that the effect still lands one frame after the match.

## Open questions

- **Derive or tabulate.** The shortest prefix can be computed at load from the word tables, or checked in as a table beside them. Which one keeps the parser's uniqueness rules in one place?
- **Which side owns the rendering.** Is the abbreviation the plugin's business — how one consumer turns an index into keystrokes — or a rendering the environment ships with each command?
- **The window shortening leaves.** Delivery is routed around, never removed. Does the step still need to wait for the match, knowing the typed phrase will always take some frames?

## Reference

| Document | What It Contains |
|----------|-----------------|
| [`../findings/command-latency.md`](../findings/command-latency.md) | The measurement this discussion follows from — the match edge, the one-frame handler, the typing-dominated wait |
| [`../../sandbox/command-latency/README.md`](../../sandbox/command-latency/README.md) | The sandbox that measured it |
| [`../../../docs/game/commands.md`](../../../docs/game/commands.md) | The abbreviation rule and Appendix B's partial list |
| [`../../../gym/emulation/plugins/daggorath/commands.lua`](../../../gym/emulation/plugins/daggorath/commands.lua) | The phrase table that turns a command index into typed text |
