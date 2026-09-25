"""Collect real experiences from the running game.

Boots the Daggorath environment headless and plays a short command script,
recording each command as one experience: the full perceived situation before
the action, the command, and the facts that changed after it, in order.
The situation is a plain object keyed by fact name, and the effects are an
array of partial states, each a subset of the situation's facts. The object
model comes from the agent's perceived-object wrapper.

Run: python agent/sandbox/knowledge-store/collect_experiences.py
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

workspace_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "gym"))
sys.path.insert(0, str(workspace_root / "agent"))

from daggorath_agent.wrappers import PerceivedObjectsWrapper
from daggorath_gym.commands import (
    NUM_OBJECT_SPECIFIERS,
    NUM_VERB_FORMS,
    DaggorathCommand,
    derive_command_index,
)
from daggorath_gym.emulator import MameConfig
from daggorath_gym.environment import DaggorathEnv
from daggorath_gym.state import PERCEIVED_FIELDS

# The scripted run.
SCRIPT = [
    "TURN LEFT",
    "EXAMINE",
    "ATTACK LEFT",
    "PULL LEFT TORCH",
    "USE RIGHT",
    "USE LEFT",
    "MOVE",
    "LOOK",
]


@dataclass
class Experience:
    """One step: the situation before, the action, and the changes after."""

    id: int
    session_id: int
    situation: dict
    action: str
    effects: list


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


def _perceived_state(observation, wrapper):
    """Return a perceived observation as a plain object keyed by fact name."""
    state = {
        field.name: int(observation["scalars"][index])
        for index, field in enumerate(PERCEIVED_FIELDS)
    }
    objects = wrapper.objects(observation)
    state["hands"] = [asdict(obj) if obj else None for obj in objects["hands"]]
    state["pack"] = [asdict(obj) if obj else None for obj in objects["pack"]]
    state["floor"] = list(objects["floor"])
    return state


def _effects(baseline, changes, wrapper):
    """Return the changed facts as an array of partial states, in order."""
    effects = []
    previous = _perceived_state(baseline, wrapper)
    for perceived in changes:
        current = _perceived_state(perceived, wrapper)
        diff = {
            name: current[name]
            for name in current
            if previous[name] != current[name]
        }
        if diff:
            effects.append(diff)
        previous = current
    return effects


def main():
    """Run the scripted torch recipe and write the real experience log."""
    environment = DaggorathEnv(mame_config=MameConfig(window=False, sound="none"))
    try:
        wrapper = PerceivedObjectsWrapper(environment)
        observation, _ = environment.reset()
        experiences = []
        for step_number, phrase in enumerate(SCRIPT, start=1):
            action = _find_action(phrase)
            baseline = observation
            observation, _, _, _, info = environment.step(action)
            experiences.append(
                Experience(
                    id=step_number,
                    session_id=1,
                    situation=_perceived_state(baseline, wrapper),
                    action=phrase,
                    effects=_effects(baseline, info["changes"], wrapper),
                )
            )
    finally:
        environment.close()

    log = {
        "session": {"id": 1, "goal": "light the torch"},
        "experiences": [asdict(experience) for experience in experiences],
    }
    output = Path(__file__).resolve().parent / "experiences.json"
    output.write_text(json.dumps(log, indent=2) + "\n")
    print(f"wrote {len(experiences)} experiences to {output}")


if __name__ == "__main__":
    main()
