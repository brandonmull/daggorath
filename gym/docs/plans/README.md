# Plans

Each plan is a single markdown file — `<topic>.md` — the pre-build design spec for that topic: *what* we're building.

## Structure

- `<topic>.md` — the design spec: *what* we're building.

Implemented plans are promoted out of this directory: their design, decision, and reasoning move into `../decisions/` — a concept-level record of what was decided and why — and the plan is removed. The plans that remain here are not yet implemented and keep their reasoning inline, in their own "Knowns" and "Decisions" sections.

## Status

| Module | Status |
|--------|--------|
| deployment | Partially implemented — registration remaining |
| creatures | Knowledge doc — sampling implemented inside the state module |
| objects | Knowledge doc — sampling implemented inside the state module |
| sound | Deferred |
| events | Deferred |
| cpp-port | Not started |
