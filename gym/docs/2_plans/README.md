# Plans

Each plan is a single markdown file — `<topic>.md` — the pre-build design spec for that topic: *what* we're building.

## Structure

- `<topic>.md` — the design spec: *what* we're building.

Implemented plans are promoted out of this directory: their design, decision, and reasoning move into `../3_decisions/` — a concept-level record of what was decided and why — and the plan is removed. The plans that remain here are not yet implemented and keep their reasoning inline, in their own "Knowns" and "Decisions" sections.

## Status

| Module | Status |
|--------|--------|
| deployment | Partially implemented — registration remaining |
| creatures | Knowledge doc — open questions in `../1_discussions/creatures.md` |
| objects | Knowledge doc — sampling implemented inside the state module |
| sound | Deferred — open questions in `../1_discussions/sound.md` |
| cpp-port | Not started — open questions in `../1_discussions/cpp-port.md` |
