#!/usr/bin/env python3
"""Fighting a monster — experiment 2 of the command-latency sandbox.

Loads the by-hand saved state where a monster is one or two cells away, then
plays ATTACK LEFT and ATTACK RIGHT in rotation as the monster closes in and
stays on the player. Every changed frame is recorded; the readings — where the
echo appeared, where the parser matched, where a watched combat field changed
— are taken from the traces afterward.

An attack always matches; it changes something only when a creature shares the
player's cell. So the trace should contain matching attacks that changed
nothing (the control) alongside any that connected.

Run: python agent/sandbox/command-latency/fighting-monster/run.py
"""

import sys
from pathlib import Path

_SANDBOX_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SANDBOX_PATH))

from harness import ScheduleEntry, run_sessions

from daggorath_gym.emulator import IpcConfig, MameConfig

# The rotation: left and right attacks, so each hand gets a turn. A miss reads
# as a match with no watched change (the control); a hit reads as a combat
# field change.
_PHRASES = ("ATTACK LEFT", "ATTACK RIGHT")

# The saved state has a monster nearby, so the schedule starts after the load
# settle (about ten seconds per the machine-save-load findings) and keeps
# posting long enough to catch the fight and the quiet after it.
_FIRST_POST_FRAME = 600
_LAST_POST_FRAME = 3000
_POST_INTERVAL = 200

_SCHEDULE = tuple(
    ScheduleEntry(frame_number=frame, phrase=_PHRASES[index % len(_PHRASES)])
    for index, frame in enumerate(
        range(_FIRST_POST_FRAME, _LAST_POST_FRAME + 1, _POST_INTERVAL)
    )
)

# The reading, applied after the run. Attacks watch the creature channels for
# a hit landed or a death, and the player's strength for a kill. m0221 is
# recorded but not watched: it recovers between hits, so it fires on heart
# recovery as well as combat.
_WATCHED_FIELDS = {
    "ATTACK LEFT": (
        "creature_damage",
        "creature_alive",
        "player_strength",
    ),
    "ATTACK RIGHT": (
        "creature_damage",
        "creature_alive",
        "player_strength",
    ),
}

# Fresh loads of the same saved state, so each session replays the encounter
# from the same moment and the spread of the offsets is the variability.
_SESSION_COUNT = 3

_IPC_CONFIG = IpcConfig(
    state_fifo_path="/tmp/daggorath-command-latency-fighting", command_port=15502
)
# The saved state lives on the CoCo 2B (the CoCo 3 cannot load states), so the
# run boots that machine and resumes the by-hand encounter.
_MAME_CONFIG = MameConfig(
    machine_name="coco2b",
    state_name="monster-near",
    window=False,
    sound="none",
)


def main():
    """Record the sessions, read the traces, and print the latency report."""
    run_sessions(
        schedule=_SCHEDULE,
        watched_fields=_WATCHED_FIELDS,
        session_count=_SESSION_COUNT,
        experiment_name="fighting-monster",
        mame_config=_MAME_CONFIG,
        ipc_config=_IPC_CONFIG,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
