"""Construct beliefs from the collected experience log.

Defines the belief shape — a situation, an action, and effects — matching the
experience's shape, so nothing is lost. Each belief is read off one experience
from the log: the full situation before the action becomes the belief's
situation, and the observed changes become the belief's effects.

Run: python agent/sandbox/knowledge-store/beliefs.py
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

_DIR = Path(__file__).resolve().parent

# The log steps that settle into beliefs: EXAMINE, PULL, USE LEFT, and the
# LOOK that reveals the lit dungeon.
_BELIEF_STEPS = (2, 4, 6, 8)


@dataclass
class Belief:
    """A settled causal claim: a situation, an action, and its effects."""

    id: int
    situation: dict
    action: str
    effects: list


def main():
    log = json.load(open(_DIR / "experiences.json"))
    experiences = {experience["id"]: experience for experience in log["experiences"]}

    beliefs = []
    for belief_id, step_id in enumerate(_BELIEF_STEPS, start=1):
        experience = experiences[step_id]
        beliefs.append(
            Belief(
                id=belief_id,
                situation=experience["situation"],
                action=experience["action"],
                effects=experience["effects"],
            )
        )

    output = {"beliefs": [asdict(belief) for belief in beliefs]}
    path = _DIR / "beliefs.json"
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(f"wrote {len(beliefs)} beliefs to {path}")


if __name__ == "__main__":
    main()
