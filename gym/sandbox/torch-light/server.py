#!/usr/bin/env python3
"""Verify torch light end-to-end: PULL LEFT TORCH, USE LEFT, check RAM values.

Drives the production plugin through MameOperator (command channel + state
FIFO + screen decode) and reports the torch/light fields at each step.

The player starts with a PINE TORCH in the backpack (grammar line 97), so
PULL LEFT TORCH always has a torch to grab. Pine torch values (ROM DA84):
minutes 15, physical light 7, magic light 0.
"""

import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from daggorath_gym.commands import _COMMAND_PHRASES, DaggorathCommand
from daggorath_gym.emulator import MameOperator, IpcConfig

IPC = IpcConfig(state_fifo_path="/tmp/daggorath-torch-light", command_port=15401)

PULL_INDEX = _COMMAND_PHRASES.index("PULL LEFT TORCH")
USE_INDEX = _COMMAND_PHRASES.index("USE LEFT")

# The lit-torch entry in the O record: class, proper, reveal, minutes,
# physical light, magic light. The torch's fields are object data now, not
# scalar fields.
_TORCH_MINUTES_INDEX = 3
_TORCH_PHYSICAL_LIGHT_INDEX = 4
_TORCH_MAGIC_LIGHT_INDEX = 5


def _receive_latest_state(operator):
    """Block until a change arrives and return the latest state."""
    while True:
        changes = operator.recv()
        if changes:
            return changes[-1][1]


def _read_until(operator, predicate, max_records=100):
    """Read states until predicate(state) is true, the cap, or a read timeout."""
    seen = []
    for _ in range(max_records):
        try:
            state = _receive_latest_state(operator)
        except TimeoutError:
            break
        seen.append(state)
        if predicate(state):
            break
    return seen


def _torch_field(state, index):
    """Read one lit-torch field; 0 when no torch is lit (or before the O record)."""
    if state.lit_torch is None:
        return 0
    return int(state.lit_torch[index])


def _print_torch_light(label, state):
    print(
        f"[{label}] torch_minutes={_torch_field(state, _TORCH_MINUTES_INDEX)} "
        f"torch_physical_light={_torch_field(state, _TORCH_PHYSICAL_LIGHT_INDEX)} "
        f"torch_magic_light={_torch_field(state, _TORCH_MAGIC_LIGHT_INDEX)} "
        f"effective_light_physical={state.effective_light_physical} "
        f"effective_light_magical={state.effective_light_magical} "
        f"ambient_light_physical={state.ambient_light_physical} "
        f"ambient_light_magical={state.ambient_light_magical} "
        f"m0221={state.m0221:#x} "
        f"player_strength={state.player_strength:#x}"
    )


def main():
    operator = MameOperator(ipc_config=IPC)
    try:
        operator.start()

        print("=== Initial state (torch unlit) ===")
        initial = _receive_latest_state(operator)
        print(f"command area: {initial.command_area_text!r}")
        _print_torch_light("initial", initial)

        # ---- Step 1: PULL LEFT TORCH (torch moves backpack → left hand) ----
        print("\n=== Step 1: PULL LEFT TORCH ===")
        operator.send(DaggorathCommand(index=PULL_INDEX))
        pull_states = _read_until(
            operator, lambda s: "PULL" in s.command_area_text.upper()
        )
        pull_state = pull_states[-1]
        print(f"command area: {pull_state.command_area_text!r}")
        _print_torch_light("after PULL", pull_state)

        # Give PULL time to finish before posting the next command.
        time.sleep(1.5)

        # ---- Step 2: USE LEFT (light the torch) ----
        print("\n=== Step 2: USE LEFT ===")
        operator.send(DaggorathCommand(index=USE_INDEX))
        use_states = _read_until(operator, lambda s: _torch_field(s, _TORCH_PHYSICAL_LIGHT_INDEX) > 0)
        lit_state = use_states[-1]
        print(f"command area: {lit_state.command_area_text!r}")
        _print_torch_light("after USE", lit_state)

        # effective_light is recomputed on the next display refresh.
        refresh_states = _read_until(
            operator, lambda s: s.effective_light_physical == 7, max_records=50
        )
        final = refresh_states[-1]
        _print_torch_light("after refresh", final)

        # ---- Checks ----
        print("\n=== Checks ===")
        torch_minutes = _torch_field(final, _TORCH_MINUTES_INDEX)
        torch_physical = _torch_field(final, _TORCH_PHYSICAL_LIGHT_INDEX)
        torch_magic = _torch_field(final, _TORCH_MAGIC_LIGHT_INDEX)
        checks = [
            ("torch_minutes in 14..15", 14 <= torch_minutes <= 15, torch_minutes),
            ("torch_physical_light == 7", torch_physical == 7, torch_physical),
            ("torch_magic_light == 0", torch_magic == 0, torch_magic),
            ("effective_light_physical == 7", final.effective_light_physical == 7, final.effective_light_physical),
            ("effective_light_magical == 0", final.effective_light_magical == 0, final.effective_light_magical),
            ("ambient_light_physical == 0", final.ambient_light_physical == 0, final.ambient_light_physical),
            ("ambient_light_magical == 0", final.ambient_light_magical == 0, final.ambient_light_magical),
        ]
        failures = []
        for name, ok, got in checks:
            print(f"{'PASS' if ok else 'FAIL'}  {name}  (got {got})")
            if not ok:
                failures.append(name)

        if failures:
            print(f"\nRESULT: FAIL ({len(failures)} check(s))")
            return 1
        print("\nRESULT: PASS")
        return 0
    finally:
        operator.stop()


if __name__ == "__main__":
    sys.exit(main())
