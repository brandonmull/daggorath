"""Generate a small log of simulated experiences for the knowledge store.

The log matches the real collector's shape: each experience is a situation,
an action, and effects, where the situation holds the perceived scalars and
the object model from the agent's wrapper. No game runs; a hand-held state
walks a short torch recipe.

Run: python agent/sandbox/knowledge-store/generate_experiences.py
"""

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

workspace_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(workspace_root / "agent"))

from daggorath_agent.wrappers import PerceivedObject

LOOK = 52838
EXAMINE = 54421


def _torch(consuming=False):
    return PerceivedObject(
        type="TORCH",
        specifier="PINE",
        revealed=True,
        consumable=True,
        consuming=consuming,
    )


def _sword():
    return PerceivedObject(
        type="SWORD",
        specifier="WOODEN",
        revealed=True,
        consumable=False,
        consuming=False,
    )


def _scalars(display, light):
    return {
        "game_mode": 0,
        "display_function": display,
        "effective_light_physical": light,
        "effective_light_magical": 0,
        "player_weight": 35,
        "player_strength": 160,
        "m0221": 0,
        "player_fainting": 0,
        "heart_beat_interval": 46,
        "evil_wizard_dead": 0,
    }


def _slots(objects, count):
    return objects + [None] * (count - len(objects))


def _serialize(objects):
    return [asdict(obj) if obj else None for obj in objects]


def _situation(scalars, hands, pack):
    state = dict(scalars)
    state["hands"] = _serialize(_slots(hands, 2))
    state["pack"] = _serialize(_slots(pack, 8))
    state["floor"] = [None] * 8
    return state


@dataclass
class Experience:
    id: int
    session_id: int
    situation: dict
    action: str
    effects: list


def main():
    sword = _sword()
    torch = _torch()
    lit_torch = _torch(consuming=True)

    hidden_pack = []
    held_pack = [sword, torch]
    sword_only_pack = [sword]
    lit_pack = [lit_torch, sword]

    steps = [
        (
            "EXAMINE",
            _situation(_scalars(LOOK, 0), [], hidden_pack),
            {
                "display_function": EXAMINE,
                "pack": _serialize(_slots(held_pack, 8)),
            },
        ),
        (
            "PULL LEFT TORCH",
            _situation(_scalars(EXAMINE, 0), [], held_pack),
            {
                "hands": _serialize(_slots([torch, None], 2)),
                "pack": _serialize(_slots(sword_only_pack, 8)),
            },
        ),
        (
            "USE LEFT",
            _situation(_scalars(EXAMINE, 0), [torch, None], sword_only_pack),
            {
                "hands": _serialize(_slots([None, None], 2)),
                "pack": _serialize(_slots(lit_pack, 8)),
            },
        ),
        (
            "LOOK",
            _situation(_scalars(EXAMINE, 0), [], lit_pack),
            {
                "display_function": LOOK,
                "effective_light_physical": 7,
                "pack": _serialize(_slots(hidden_pack, 8)),
            },
        ),
    ]

    experiences = []
    for step_number, (action, situation, effect) in enumerate(steps, start=1):
        experiences.append(
            Experience(
                id=step_number,
                session_id=1,
                situation=situation,
                action=action,
                effects=[effect],
            )
        )

    log = {
        "session": {"id": 1, "goal": "light the torch"},
        "experiences": [asdict(experience) for experience in experiences],
    }
    output = Path(__file__).resolve().parent / "experiences.simulated.json"
    output.write_text(json.dumps(log, indent=2) + "\n")
    print(f"wrote {len(experiences)} experiences to {output}")


if __name__ == "__main__":
    main()
