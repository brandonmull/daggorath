#!/usr/bin/env python3
"""Lighting a torch — experiment 1 of the command-latency sandbox.

Records the torch-lighting sequence — PULL LEFT TORCH, then USE LEFT — in
three fresh sessions. Each session records every changed frame the game
reports; the readings (where the echo appeared, where the parser matched,
where the light or the holdings changed) are taken from the traces afterward.

The player starts with a PINE TORCH in the backpack, so both commands are
deterministic and the expected effect can be named before the run.

Run: python agent/sandbox/command-latency/lighting-torch/run.py
"""

import sys
from pathlib import Path

_SANDBOX_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SANDBOX_PATH))

from harness import ScheduleEntry, run_sessions

from daggorath_gym.emulator import IpcConfig, MameConfig

_SCHEDULE = (
    ScheduleEntry(frame_number=1100, phrase="PULL LEFT TORCH"),
    ScheduleEntry(frame_number=2000, phrase="USE LEFT"),
)

# The reading, applied after the run: the columns that count as each command's
# effect. PULL moves the torch between pack and hand and touches no light;
# USE lights the torch and the dungeon's visible physical light.
_WATCHED_FIELDS = {
    "PULL LEFT TORCH": ("hands", "pack"),
    "USE LEFT": ("lit_torch", "effective_light_physical"),
}

# Fresh boots, so each session replays from the game's deterministic opening.
_SESSION_COUNT = 3

_IPC_CONFIG = IpcConfig(
    state_fifo_path="/tmp/daggorath-command-latency", command_port=15501
)
_MAME_CONFIG = MameConfig(window=False, sound="none")


def main():
    """Record the sessions, read the traces, and print the latency report."""
    run_sessions(
        schedule=_SCHEDULE,
        watched_fields=_WATCHED_FIELDS,
        session_count=_SESSION_COUNT,
        experiment_name="lighting-torch",
        mame_config=_MAME_CONFIG,
        ipc_config=_IPC_CONFIG,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
