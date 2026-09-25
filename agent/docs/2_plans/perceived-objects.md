# Perceived Objects — Plan

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The environment reports objects as specifier indices in the hands and pack channels, and it reports the lit torch's identity, minutes, and light in the true-state record. The agent wants each object as five fields, a type, a specifier, and three flags in a fixed order. This plan adds the agent-side wrapper that does the translation, and it is the default. A developer who wants a different object schema edits this wrapper, never the environment.

The game facts the translation builds on live in [`../../../docs/game/objects.md`](../../../docs/game/objects.md). This doc specifies only the default schema and the rules that produce it.

## The object shape

Each object the agent possesses, in a hand or the pack, becomes one structure. A floor object stays a bare class, because the game's 3D view draws it as a picture keyed by class alone, never by proper name or reveal state.

- `type`: the class, TORCH, SWORD, SHIELD, FLASK, SCROLL, or RING.
- `specifier`: the proper name, PINE, WOODEN, MITHRIL, and the rest, or null while unrevealed.
- `revealed`: whether the proper name is shown.
- `consumable`: whether the object's resource can still be spent.
- `consuming`: whether the resource is being spent now. Torch only.

The flags come in that order because it is the lifecycle: know it, have it, spend it. `revealed` first, then `consumable`, then `consuming`, and a later stage holds only after the earlier ones.

The rename-states stay folded into the specifier. Reveal, incantation, flask drinking, and torch burn-out all change the name, so the agent reads them off the name, and the flags carry only what the name does not.

## The translation

The wrapper reads the perceived hands and pack for the specifier indices, the floor objects for their class, and the true-state lit-torch record for the lit torch's identity, minutes, and light.

```
PerceivedObjectsWrapper
    → walks the hands and the pack, and resolves each possessed object
        → a bare-class index gives the class and a null specifier
        → a proper-name index gives the class and the proper name
    → sets revealed from whether the specifier is present
    → resolves the lit torch by matching its identity against the pack
    → on the lit torch, sets consuming and consumable from its minutes
    → for every other possessed object, sets consumable by type
        → a flask stays consumable unless its name reads EMPTY
        → a ring stays consumable unless its name reads GOLD
        → a torch stays consumable unless its name reads DEAD
    → derives each floor object's class from its specifier, dropping the proper name and reveal state
```

## Default choices

The translation is held as explicit constants, the class names, the proper-name tokens, the spent markers, so a developer reads and edits them. Changing the schema means changing the wrapper, not the environment.

Two defaults are approximations and are called out:

- A non-lit torch's consumable reads "not DEAD" rather than its exact minutes, because the pack ships class, proper, and reveal only. The lit torch's minutes ride on the true-state record and give the exact answer for that one torch. Exact minutes for every torch need the environment to ship the special data.
- The lit torch is resolved by matching its identity against the pack. With one torch that is exact; with two identical torches it is ambiguous, and the precise signal is the game's torch pointer, which is not shipped.

## Where it lands

- `agent/daggorath_agent/wrappers.py` — `PerceivedObjectsWrapper` and the constants.
- The environment is unchanged.

## Open questions

- Ship each torch's minutes so consumable is exact for non-lit torches.
- Ship the torch pointer so two identical torches resolve exactly.
- Whether the environment should report the floor-object class rather than the specifier, since the 3D view draws class pictures. Until then the wrapper derives the class itself.

## Reference Documents

| Document | What it contains |
|---|---|
| [`../../../docs/game/objects.md`](../../../docs/game/objects.md) | The game's object classes, names, and states |
| [`perceived-creatures.md`](perceived-creatures.md) | The sibling wrapper and the agent-side shaping boundary |
| [`../3_decisions/observation-wrapper.md`](../3_decisions/observation-wrapper.md) | The existing wrapper decision |
