"""Chain beliefs by matching effects against situations.

Loads the beliefs and, for each one, finds the beliefs whose situation
matches one of its effects. The pack matches as an unordered set of objects
and the floor as an unordered set of classes; hands and scalars match
exactly.

Run: python agent/sandbox/knowledge-store/chain.py
"""

import json
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).resolve().parent


def _nonempty(items):
    return [item for item in items if item is not None]


def _object_key(obj):
    return json.dumps(obj, sort_keys=True)


def _same(actual, expected, fact):
    if fact == "pack":
        return Counter(_object_key(obj) for obj in _nonempty(actual)) == Counter(
            _object_key(obj) for obj in _nonempty(expected)
        )
    if fact == "floor":
        return set(_nonempty(actual)) == set(_nonempty(expected))
    return actual == expected


def _matches(situation, effect):
    return all(
        _same(situation.get(fact), value, fact) for fact, value in effect.items()
    )


def next_beliefs(belief, beliefs):
    others = [b for b in beliefs if b["id"] != belief["id"]]
    matched = set()
    for effect in belief["effects"]:
        for other in others:
            if _matches(other["situation"], effect):
                matched.add(other["id"])
    return [b for b in others if b["id"] in matched]


def main():
    beliefs = json.load(open(_DIR / "beliefs.json"))["beliefs"]
    for belief in beliefs:
        nxt = [f"{b['id']} {b['action']}" for b in next_beliefs(belief, beliefs)]
        print(f"belief {belief['id']} {belief['action']:<16} -> {nxt}")


if __name__ == "__main__":
    main()
