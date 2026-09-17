#!/usr/bin/env python3
"""Causal-diff probe: verify the state diff and the cause/effect split.

Drives the real Daggorath environment through the torch-lighting event —
PULL LEFT TORCH, then USE LEFT — and reads the distinct perceived changes
each command returns from the environment's step. It checks that the change
set recovers each step — the torch in hand, then the light on — with every
other change reported as noise.

Run: python agent/sandbox/causal-diff/server.py
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
from daggorath_gym.state import PERCEIVED_FIELDS

# The torch event splits across the fact/valuation boundary. The perceived
# effect — what the player sees — is effective_light_physical rising as the
# dungeon brightens. The primitive cause — what USE writes directly — is the
# torch's own light, a true-state fact in the lit-torch object record
# (physical light sits at index 4 of the 6-byte torch entry). Every other
# perceived scalar that changes — the heartbeat, the tiredness — is noise.
_PERCEIVED_EFFECT_FIELDS = ("effective_light_physical",)
_TORCH_PHYSICAL_LIGHT_INDEX = 4

# Field name -> its position in the perceived scalars array.
_FIELD_INDEX = {field.name: index for index, field in enumerate(PERCEIVED_FIELDS)}


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
    """Label a changed scalar field: effect or noise."""
    if name in _PERCEIVED_EFFECT_FIELDS:
        return "effect"
    return "noise"


def _hand_slots(observation):
    """Return the two hand slot values (0xFF for an empty hand)."""
    hands = observation["hands"]
    return [int(hands[0]), int(hands[1])]


def _hand_holds_torch(observation):
    """True when a hand holds an object (the torch, in this scripted run)."""
    hands = observation["hands"]
    return int(hands[0]) != 0xFF or int(hands[1]) != 0xFF


def _action_phrase(action):
    """Return the command phrase for a factored action (for the report only)."""
    command_index = derive_command_index(int(action[0]), int(action[1]))
    return DaggorathCommand(index=command_index).phrase


def _read_change_set(environment, action):
    """Step the command and return the settled observation, changes, and frames."""
    observation, _, _, _, info = environment.step(action)
    return observation, info["changes"], info["frames"]


def _report_command(action, scalar_changes, change_count, frames, hand_before, hand_after):
    """Print the change set for one command, with classifications."""
    verb_form, object_specifier = int(action[0]), int(action[1])
    print(
        f"\ncommand verb {verb_form}, object {object_specifier}  "
        f"({_action_phrase(action)})"
    )
    print(f"  {change_count} distinct perceived changes, frames {frames}")
    if hand_before != hand_after:
        before = "[" + ", ".join("0xFF" if slot == 0xFF else str(slot) for slot in hand_before) + "]"
        after = "[" + ", ".join("0xFF" if slot == 0xFF else str(slot) for slot in hand_after) + "]"
        print(f"  hands: {before} -> {after}")
    if not scalar_changes:
        print("  (no scalar fields changed)")
        return
    for name in sorted(scalar_changes, key=lambda field_name: _FIELD_INDEX[field_name]):
        before, after = scalar_changes[name]
        print(f"  {name:<24} {before} -> {after}   [{_classify_field(name)}]")


_PULL_ACTION = _find_action("PULL LEFT TORCH")
_USE_ACTION = _find_action("USE LEFT")


def main():
    """Run the probe and return 0 on pass, 1 on fail."""
    environment = DaggorathEnv(mame_config=MameConfig(window=False, sound="none"))
    try:
        observation, _ = environment.reset()

        baseline = _scalar_values(observation)
        print("Causal-diff probe: torch-lighting event")
        print(f"baseline: effective_light_physical={baseline['effective_light_physical']}")

        failures = []
        for name in _PERCEIVED_EFFECT_FIELDS:
            if baseline[name] != 0:
                failures.append(
                    f"baseline {name} is {baseline[name]}, expected 0 (dungeon dark)"
                )

        # PULL LEFT TORCH: move the torch to hand. No torch field may change.
        before_pull = _scalar_values(observation)
        before_pull_hands = _hand_slots(observation)
        observation, pull_change_set, pull_frames = _read_change_set(environment, _PULL_ACTION)
        pull_scalar_changes = _diff_scalar_fields(before_pull, _scalar_values(observation))
        _report_command(
            _PULL_ACTION, pull_scalar_changes, len(pull_change_set), pull_frames,
            before_pull_hands, _hand_slots(observation),
        )
        if not any(_hand_holds_torch(change) for change in pull_change_set):
            failures.append("PULL did not put the torch in hand")
        for name in _PERCEIVED_EFFECT_FIELDS:
            if name in pull_scalar_changes:
                failures.append(f"PULL changed {name}; the dungeon brightened before USE")

        # USE LEFT: light the torch.
        before_use = _scalar_values(observation)
        before_use_hands = _hand_slots(observation)
        observation, use_change_set, use_frames = _read_change_set(environment, _USE_ACTION)
        after_use = _scalar_values(observation)
        use_scalar_changes = _diff_scalar_fields(before_use, after_use)
        _report_command(
            _USE_ACTION, use_scalar_changes, len(use_change_set), use_frames,
            before_use_hands, _hand_slots(observation),
        )

        # Success criteria: the perceived effect (effective_light_physical) goes
        # 0 -> N as the single change, and the true-state cause (the torch's
        # own light) is now on. Every other change — heartbeat, tiredness — is
        # noise, reported but not failed.
        light_change = use_scalar_changes.get("effective_light_physical")
        if light_change is None or light_change[0] != 0 or light_change[1] <= 0:
            failures.append("effective_light_physical did not go 0 -> N (dungeon stayed dark)")
        torch_light = int(environment.current_state.lit_torch[_TORCH_PHYSICAL_LIGHT_INDEX])
        if torch_light <= 0:
            failures.append("the lit torch's physical light is 0; USE did not light it")

        if failures:
            print("\nRESULT: FAIL")
            for failure in failures:
                print(f"  - {failure}")
            return 1
        print("\nRESULT: PASS — the dungeon brightened (perceived), the torch lit (true state)")
        return 0
    finally:
        environment.close()


if __name__ == "__main__":
    sys.exit(main())
