# Project: Daggorath

Training an RL bot to play Dungeons of Daggorath (1982) in MAME + Gymnasium.

**⚠️ READ `gym/README.md` first** — it contains the full project overview, architecture, milestones, and directory structure. This file provides supplemental AI-specific constraints.

## Platform
- Windows 11 + WSL (Ubuntu)
- MAME runs in WSL, WSLg provides display
- No Docker — project runs bare-metal on WSL
- For headless training: `-video none -sound none`

## Git
- **Never commit to git** — do not run `git add`, `git commit`, or any git command that modifies the repository. The user handles all git operations.
- **Commit messages stay terse and conventional** — a short summary line, then a brief body at most. The summary names what the work delivers, the body says what it does and, when the commit carries one, what it found. No file lists, no bulleted change-lists, no documentation.
- **Write the deed, not the token** — the body names what a command does ("pulling the torch", "lighting it"), not the game phrase or the code identifier, and uses the project's own vocabulary (`matched`, `written`, `executed`). Quote a name only when the change is about that name. Every verb keeps its object, and no term of art goes unexplained.

  ```
  feat: add the torch command-latency experiment

  Records commands for pulling the torch and lighting it across three fresh
  boots, and writes up the findings: the effect lands one frame after the
  command is matched.
  ```

## MAME & Lua
- **MAME uses its own embedded Lua** — not the system Lua. LuaRocks packages cannot be loaded. Don't suggest LuaRocks.

## Package Boundary
- **The import boundary is the split.** `daggorath_gym` imports only `gymnasium` and `numpy`; only `daggorath_agent` imports the training stack (`stable-baselines3`, `torch`, `sb3-contrib`). Never add a training import to the environment.
- **Fact vs. valuation.** The environment reports facts and returns reward 0.0; reward is an agent-side valuation. The agent reads true state through the environment's `current_state` property — never through RAM addresses or disassembly. It consumes the interface, not the internals.

- **Fact vs. attribution.** The environment reports the perceived changes in order, with the frame where each began, and makes no claim about what caused each one. Attribution — telling a command's effect from the world's own motion — is agent-side, like valuation. Heart, exertion, and the torch's burn stay perceived; the environment never filters cause from noise.
- **Checkpoint policy.** Trained weights land in `agent/checkpoints/` (gitignored); never commit them.

## Documentation

- **Tiers.** Game knowledge and shared principles live in `docs/`; the environment's design (facts, observation machinery) lives in `gym/docs/`; the trainer's design — including the reward — lives in `agent/docs/`. Reward is agent-side: its code and docs live in `agent/`, never in `gym/`.

- **Numbered lifecycle: `1_discussions` → `2_plans` → `3_decisions`.** An idea is first discussed (open questions, not-yet-decided), then planned (a pre-build spec), then decided (implemented, with the reasoning). No review tier, no conversation files.

- **Flat by default.** Docs are `<topic>.md` files, not `<topic>/plan.md` — a folder wrapping a single file is redundant. Use a folder only when a topic genuinely needs multiple related files (e.g. `2_plans/curriculum/` and its courses).

- **Consolidate, don't proliferate.** Prefer extending an existing doc over adding a new one. If a discovery extends a subject a file already covers, add a section there; a new file is for a subject that has no home yet.

- **A concept may span stages** — e.g. `1_discussions/creatures.md` (open questions) plus `2_plans/creatures.md` (the spec), or `3_decisions/deployment.md` (what shipped) plus `2_plans/deployment.md` (what remains).

- **Promote on completion.** When a plan's work ships, fold its design and reasoning into a decision and remove the plan (or trim it to what remains). Beside the pipeline sit `findings/` (hard-won discoveries) and `references/` (external source material).

## Coding Conventions
- **Naming conventions are binding.** The global rule governs meaning; these are the project's conventions on top of it. Lua uses camelCase; Python uses snake_case. Spell full words, never abbreviations (`_state_connection`, not `_state_conn`; `socket`, not `sock`). Multi-word names follow adjective-then-noun order (`state_socket`, not `socket_state`). `gym/README.md` is the authority — check it before choosing any name.

- **Schema names supply meaning; reference docs keep the game's names.** A wire field name says what the value means (`command_parser_position`), not where it lives or what the game calls its RAM byte (`m0211`). The reference docs stay faithful to the game's names, and `ram-signals.md` carries the names table that bridges them.
- **Verb+object method names.** Methods that do work should name what they act on: `_create_listening_socket(port)`, not `_bind()` or `_create_server()`.
- **`local` all Lua variables.** Including module requires: `local state = require("state")`.
- **No speculative API surface.** Don't add methods, properties, or context-manager protocols unless a real caller exists. Delete unused surface rather than leaving it for "later."
- **Module docstrings are broad; class docstrings are specific.** No duplication between them. Class docstrings describe spaces, lifecycle, and current status.
- **No cross-layer implementation comments.** Python code describes its own rationale, not Lua internals. Lua code describes its own rationale, not Python expectations. Each layer documents itself.

## AI Implementation Constraints
- **Implement only what the plan specifies.** Do not add configurability, defaults, extra exports, or structural abstractions that the plan does not ask for. The plan is the specification — build to it, not past it.
- **Each package's `__init__.py` exports only what its known consumer needs.** `daggorath_gym` exports `DaggorathEnv` (what Stable-Baselines3 requires); `daggorath_agent` exports nothing — it is run, not imported.

## Reference Docs
- **Game knowledge lives in `docs/game/`** — `commands.md` (command grammar), `levels.md` (level maps), `combat-model.md` (strength-vs-damage).
- **Observation machinery lives in `gym/docs/references/`** — `game/ram.md` (RAM map), `game/code.md` (6809 disassembly), `coco/hardware.md`, `mame/setup.md`, `mame/lua-common.md`, `mame/lua-core.md`, `mame/keyboard.md`.
- **Reference docs are faithful transcriptions of the original source material.** When converting external documentation (MAME docs, hardware specs, game manuals) to markdown, transcribe the full content exactly as published. Do not filter, summarize, editorialize, or add project-specific commentary. Do not omit sections. The purpose of a reference doc is to mirror the original — the reader expects the complete source, not a curated subset.

## README Writing Principles

When writing or revising README files:

1. **Order sections by the reader's questions, in sequence.**
   The reader's mental path is: What is this? → Can I install it? → What's broken? → Where is it going? → How does it work? → Where's the deep dive? Structure follows that inquiry order — not the structure of the codebase, not the history of the project.

2. **The getting-started path comes immediately after the intro.**
   If someone can't install and run in under a minute, they'll leave. Everything else — architecture, roadmap, reference docs — is secondary.

3. **If a section has only 2-3 items, it's probably a sub-point.**
   Tiny sections with few bullet points are visual clutter. Fold them into the nearest related section. Headings are expensive — don't spend them on trivia.

4. **Be honest about limitations before presenting aspirations.**
   Known Issues goes before Milestones. A roadmap that paints an optimistic picture while hiding bugs erodes trust. The contract is "here's what's broken" — everything else is hope.

5. **Never present the same information twice.**
   If a directory tree and a manifest table both answer "where are the files," keep the more scannable one. Duplication makes readers wonder if they missed a difference — there is no difference, it's just noise.

6. **Every section must justify its existence.**
   Remove a section when its content answers a question already answered elsewhere, or when it's too thin to stand alone. Sections serve content, not convention.

7. **Write, challenge, rewrite.**
   The first draft is scaffolding. The collaborative back-and-forth is the real writing process. The final result is leaner than anything produced alone in one pass.

## Plan Doc Writing Principles

When writing or revising files in `gym/docs/2_plans/` or `agent/docs/2_plans/`:

1. **Be specific about scope.**
   Every instruction should define what it applies to. Instead of "use `command` everywhere," say what domain the rule governs: "components related to how the player issues commands." The reader shouldn't have to guess where the boundary is.

**Naming and Terminology**

2. **Follow the coding conventions in `gym/README.md`.**
   The README documents the project's coding conventions, including naming. Plan docs must use the names prescribed there.

**Document Structure**

3. **Implementation details live in module docs, not in the overview.**
   `docs/overview.md` sets project-wide conventions and principles. Per-module specifics — constants, function signatures, class attributes — belong in that module's own plan doc.

4. **No source code in plan docs.**
   A plan is a design document, not an implementation. Describe what the code should do, name the important constants/classes/functions, but never paste Lua or Python source. Code blocks are for architecture diagrams, pseudo-code, and data flow — not executable code.

**Code Structure**

5. **Don't extract a subset into a separate constant when the superset already exists.**
   If a set of values is derivable from an existing constant, the filter lives in the function that uses it — not in a duplicate constant that must be kept in sync.

6. **Prefer tuples for simple data, but use a named type when position alone isn't clear.**
    A tuple works when each element's role is obvious from context. When the reader would need to remember which position means what, a dataclass or named tuple reduces cognitive load.

7. **Don't add structure the plan doesn't ask for.**
    If the plan defines a module with three constants, implement those three. If you see an opportunity to extract a helper, rename for consistency, or add a constant that seems useful — ask first. Don't silently diverge from the plan. The plan names things: use those exact names. The other side's corresponding module (commands.lua ↔ commands.py) is the second source of truth — they must mirror each other identically.

**How to Write**

8. **Don't repeat data that already appears elsewhere in the same doc.**
   If earlier sections define all the relevant values, later sections reference them rather than reprinting them.

9. **Lead with prose, not with symbol lists.**
    When presenting constants, functions, or class attributes, describe them in flowing text first. A list may follow for reference, but it never stands alone as a section's content.

10. **Use arrow notation for behavior descriptions.**
    Function names head each block. Arrows describe what happens using plain language —
    no variable names, table keys, or code identifiers in the arrow text:

    ```
    function_name()
        → walks each object class
        → for each class, adds the bare class name as a specifier
        → then adds each proper name followed by its class
        → returns 31 specifiers
    ```

    This is easier to scan than prose paragraphs and avoids the symbol-index problem
    (walls of `_BACKTICKED_IDENTIFIERS`). Every arrowed item is plain English;
    code symbols live in the block title, not the body.

## Discussion Doc Writing Principles

When writing or revising files in `gym/docs/1_discussions/` or `agent/docs/1_discussions/`:

1. **Record the exchanges, not just the conclusions.**
   A discussion doc keeps the argument — the question asked, the answer given, and the reply — in the words that produced it, lightly cleaned. The reader follows *how* a conclusion was reached, not just what it was. That is what makes a discussion a discussion and not a decision.

2. **Format every exchange as a blockquote of labeled turns.**
   Each turn is a bolded descriptive label, an em-dash, and the quoted words; a lone `>` separates turns:

   ```
   > **the question** — "…"
   >
   > **the answer** — "…"
   ```

   One blockquote per exchange, introduced by a one-line lead-in.

3. **Label turns by what they do, not who speaks.**
   `the premise`, `the answer`, `the doubt`, `the proposal`, `the agreement`, `the objection`, `the correction` — never "user" or "assistant". Labels stay lowercase, matching the existing docs.

4. **Every turn answers something present; every block has a lead-in.**
   A reply with nothing to reply to reads as a non-sequitur. If a turn responds to a statement, quote the statement first — and a block with a single turn still needs its lead-in, such as "The reasoning was stated plainly:".

5. **Clean the quotes; keep the voice.**
   Fix capitalization, grammar, and spelling (American — `behavior`, `recognize`, `colored`). Capitalize every sentence, including one that would otherwise begin with a lowercase code identifier — rephrase so it opens with a word. Keep contractions and spoken register; a quote that reads like an essay is no longer a quote.

6. **Gloss after the block; don't repeat it.**
   Follow each block with prose that adds the implication. Where the quote already says something, the prose carries it forward rather than restating it, and puts the ideas in its own words — a gloss built from the quote's phrasing adds nothing the quote didn't already say.

7. **The lead-in states the purpose and the payoff.**
   Open a block by naming what prompted the exchange and previewing the insight it produced. Keep it to a couple of plain sentences — concrete, not a bland label ("a review"), and without em dashes or colons as ornament.

8. **The prose is impersonal; the quotes carry the voice.**
   The turns speak in the first person ("I think…", "One session, in my mind…"), but the prose around them never names a participant. Never write "the author" or "the user" — describe the exchange impersonally.

9. **The titles alone tell the story.**
   A reader scanning the section titles should be able to follow the argument — the cohesion has to be visible at the outline, not buried in a paragraph. Order the sections as a chain in which each is the next step from the one before.

10. **A section answers its title, and only its title.**
    Don't let it drift into a second question. When a consequence or fallout appears that the title doesn't cover — how one lesson's knowledge combines with another's, say — give it its own question or move it to Open questions.

11. **Order framing before detail, and keep one artifact to one section.**
    A section that frames what follows — a layering, a roadmap — belongs ahead of the detail it frames. When two sections re-enter the same artifact, merge them rather than stack them.

12. **Title with the reader's own question, and name the subject.**
    Prefer the question a reader would actually ask ("When is one step finished?") over a clinical label ("The step unit"), and keep titles in sentence case. No title leans on a pronoun that reaches back to an earlier title ("part of it", "the two", "that graph") — each names what its own section is about.

13. **A title must ask something worth answering.**
    If nobody could doubt the answer, the title isn't a question — it's a decision wearing one. State the real choice, with the rejected alternative visible: "Should a consumer reuse the environment's state reporting, or repeat that work for itself?" A forced question tells the reader nothing and flattens the outline.

14. **Conclusions stand on their own.**
    The prose that closes a section states its claim whole, naming its subject. No stubs ("No, then"), no bare pro-forms ("one", "the two"), and no leaning on an earlier section to supply what's missing. A reader who reads only the closing sentence should still get the conclusion. The rule against titles leaning on pronouns applies to conclusions too.

15. **Divide by move, not by topic.**
    Cut a discussion into the steps of its argument — each section the step the previous answer forces — not into a list of subjects. A topic list cannot narrate however its titles are worded; a chain of moves can.

16. **Restate; do not reference.**
    No "Section 1", "the two sections before", "the gap", "as above". Say the thing itself wherever it is needed. A reference sends the reader backward and breaks the sentence for anyone reading it alone.

17. **Quotes keep the words that were said; the prose generalizes.**
    Clean a quote's grammar, never its vocabulary. If a turn said "sandbox", it keeps saying "sandbox" after the prose has adopted a broader term; retrofitting a quote rewrites the record and hides the conversation's own vocabulary.

18. **Hold one question form across the headings.**
    Sections read as a chain when they share a shape. Mixing "Does…?", "Why…?", "What…?", and "Should…?" reads as a list even when the argument isn't one. Fix the form and let the answers carry the variation.

## Seed Prompt Writing Principles

When writing a seed prompt to hand the work to a fresh session:

1. **The goal comes first, stated plainly.**
    Open with the concrete task the new session must do, in plain words. No preamble — a seed prompt is a handoff, not an introduction.

2. **Don't restate the project's purpose.**
    The repo already says what this project is (`README` and this file). Repeating "we're training an RL agent to play Daggorath" burns the opening on something the reader can see for itself.

3. **Keep it short.**
    A seed is a pointer, not a briefing: the goal, the current state in a sentence or two, and the next step. The reader hunts down the rest.

4. **Name only the critical references.**
    One or two files that frame the current work — the README or plan that matters now — and stop. The reader follows links and searches; a wall of references is a briefing again.
