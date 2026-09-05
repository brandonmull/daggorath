#!/usr/bin/env python3
"""Ground-truth probe: verify the state diff and the primitive-field choice.

Drives the real Daggorath environment through the torch-lighting event —
PULL LEFT TORCH, then USE LEFT — and diffs the perceived scalar fields
before and after each command. It checks that the USE diff recovers
"light the torch" as one primitive cause (`torch_physical_light`), with every
other change reported as noise.

Run: python agent/sandbox/ground-truth-probe/server.py
"""

import sys
from pathlib import Path

import numpy as np

workspace_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "gym"))

from daggorath_gym.commands import (
    NUM_OBJECT_SPECIFIERS,
    NUM_VERB_FORMS,
    DaggorathCommand,
    derive_command_index,
)
from daggorath_gym.emulator import MameConfig
from daggorath_gym.environment import DaggorathEnv
from daggorath_gym.state import FIELDS

# The torch event's primitive cause. The disassembly is the authority
# (gym/docs/references/game/code.md): torch_physical_light is the number USE
# writes into the lit torch's object slot. Every other scalar that changes —
# the heartbeat, the tiredness, the burn-down timer — is noise.
_PRIMITIVE_FIELDS = ("torch_physical_light",)

# Maximum no-op frames to wait for a command's effect to settle before failing.
_SETTLE_STEPS = 100

# Field name -> its position in the perceived scalars array (FIELDS order).
_FIELD_INDEX = {name: index for index, (name, _, _) in enumerate(FIELDS)}


def _find_action(phrase):
    """Return the factored action (verb form, object specifier) for a phrase."""
    for verb_form in range(NUM_VERB_FORMS):
        for object_specifier in range(NUM_OBJECT_SPECIFIERS):
            command_index = derive_command_index(verb_form, object_specifier)
            if (
                command_index is not None
                and DaggorathCommand(index=command_index).phrase == phrase
            ):
                return np.array([verb_form, object_specifier], dtype=np.int64)
    raise ValueError(f"No factored action maps to command phrase {phrase!r}")


def _find_noop_action():
    """Return a syntactically invalid action — sends nothing, still advances a frame."""
    for verb_form in range(NUM_VERB_FORMS):
        for object_specifier in range(NUM_OBJECT_SPECIFIERS):
            if derive_command_index(verb_form, object_specifier) is None:
                return np.array([verb_form, object_specifier], dtype=np.int64)
    raise RuntimeError("No syntactically invalid action exists")


def _scalar(observation, name):
    """Read one scalar field by name from a perceived observation."""
    return int(observation["scalars"][_FIELD_INDEX[name]])


def _scalar_values(observation):
    """Return the perceived scalars as a {field name: value} mapping."""
    scalars = observation["scalars"]
    return {name: int(scalars[index]) for name, index in _FIELD_INDEX.items()}


def _diff_scalar_fields(before, after):
    """Return {field name: (before, after)} for scalar fields that changed."""
    return {
        name: (before[name], after[name])
        for name in before
        if before[name] != after[name]
    }


def _classify_field(name):
    """Label a changed scalar field: cause or noise."""
    if name in _PRIMITIVE_FIELDS:
        return "cause"
    return "noise"


def _hand_slots(observation):
    """Return the two hand slot values (0xFF for an empty hand)."""
    hands = observation["hands"]
    return [int(hands[0]), int(hands[1])]


def _hand_holds_torch(observation):
    """True when a hand holds an object (the torch, in this scripted run)."""
    hands = observation["hands"]
    return int(hands[0]) != 0xFF or int(hands[1]) != 0xFF


def _torch_lit(observation):
    """True once the torch's own light is on — the primitive cause."""
    return _scalar(observation, "torch_physical_light") > 0


def _action_phrase(action):
    """Return the command phrase for a factored action (for the report only)."""
    command_index = derive_command_index(int(action[0]), int(action[1]))
    return DaggorathCommand(index=command_index).phrase


def _step_until_settled(environment, observation, predicate):
    """Step no-op frames until predicate(observation) holds, or the cap/timeout."""
    for _ in range(_SETTLE_STEPS):
        if predicate(observation):
            return observation
        try:
            observation, _, _, _, _ = environment.step(_NOOP_ACTION)
        except TimeoutError:
            break
    return observation


def _report_command(action, changes, hand_before, hand_after):
    """Print which channels changed for one command, with classifications."""
    verb_form, object_specifier = int(action[0]), int(action[1])
    print(
        f"\ncommand verb {verb_form}, object {object_specifier}  "
        f"({_action_phrase(action)})"
    )
    if hand_before != hand_after:
        before = "[" + ", ".join("0xFF" if slot == 0xFF else str(slot) for slot in hand_before) + "]"
        after = "[" + ", ".join("0xFF" if slot == 0xFF else str(slot) for slot in hand_after) + "]"
        print(f"  hands: {before} -> {after}")
    if not changes:
        print("  (no scalar fields changed)")
        return
    for name in sorted(changes, key=lambda field_name: _FIELD_INDEX[field_name]):
        before, after = changes[name]
        print(f"  {name:<24} {before} -> {after}   [{_classify_field(name)}]")


_PULL_ACTION = _find_action("PULL LEFT TORCH")
_USE_ACTION = _find_action("USE LEFT")
_NOOP_ACTION = _find_noop_action()


def main():
    """Run the probe and return 0 on pass, 1 on fail."""
    environment = DaggorathEnv(mame_config=MameConfig(window=False, sound="none"))
    try:
        observation, _ = environment.reset()

        baseline = _scalar_values(observation)
        print("Ground-truth probe: torch-lighting event")
        print(f"baseline: torch_physical_light={baseline['torch_physical_light']}")

        failures = []
        for name in _PRIMITIVE_FIELDS:
            if baseline[name] != 0:
                failures.append(
                    f"baseline {name} is {baseline[name]}, expected 0 (torch not unlit)"
                )

        # PULL LEFT TORCH: move the torch to hand. No torch field may change.
        before_pull = _scalar_values(observation)
        before_pull_hands = _hand_slots(observation)
        observation, _, _, _, _ = environment.step(_PULL_ACTION)
        observation = _step_until_settled(environment, observation, _hand_holds_torch)
        if not _hand_holds_torch(observation):
            failures.append("PULL did not put the torch in hand")
        pull_changes = _diff_scalar_fields(before_pull, _scalar_values(observation))
        _report_command(
            _PULL_ACTION, pull_changes, before_pull_hands, _hand_slots(observation)
        )
        for name in _PRIMITIVE_FIELDS:
            if name in pull_changes:
                failures.append(f"PULL changed {name}; the torch lit before USE")

        # USE LEFT: light the torch.
        before_use = _scalar_values(observation)
        before_use_hands = _hand_slots(observation)
        observation, _, _, _, _ = environment.step(_USE_ACTION)
        observation = _step_until_settled(environment, observation, _torch_lit)
        after_use = _scalar_values(observation)
        use_changes = _diff_scalar_fields(before_use, after_use)
        _report_command(_USE_ACTION, use_changes, before_use_hands, _hand_slots(observation))

        # Success criterion: torch_physical_light 0 -> N as the single cause.
        # Every other change — heartbeat, tiredness, the burn-down timer — is
        # noise, reported but not failed.
        torch_change = use_changes.get("torch_physical_light")
        if torch_change is None or torch_change[0] != 0 or torch_change[1] <= 0:
            failures.append("torch_physical_light did not go 0 -> N as the single cause")

        if failures:
            print("\nRESULT: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("\nRESULT: PASS — one cause, the rest noise")
        return 0
    finally:
        environment.close()


if __name__ == "__main__":
    sys.exit(main())