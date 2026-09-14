#!/usr/bin/env python3
"""Launcher for the by-hand machine save-load experiment.

Opens MAME windowed with the state directory pointed at the project's, the Lua
console enabled, and no plugin at all: the point is for a person to play and
save, so nothing should be posting keystrokes of its own. The console prompt
appears in this terminal while the game runs in the window, and takes
machine:save and machine:load — which is what lets a by-hand state carry a
name of its own.

--autosave adds the fallback: MAME then writes auto.sta as it exits, one slot,
restored again on the next start.

Run: python gym/sandbox/machine-save-load/manual/run.py [--autosave]
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import GYM_PATH, MACHINE_NAME, STATE_DIRECTORY

AUTOSAVE_FLAG = "--autosave"


def _state_files():
    """The saved states on disk, in name order."""
    if not STATE_DIRECTORY.exists():
        return []
    return sorted(STATE_DIRECTORY.rglob("*.sta"))


def _build_command(autosave):
    """Assemble the MAME command line for a by-hand session."""
    command = [
        "mame", MACHINE_NAME, "daggorath",
        "-rompath", str(GYM_PATH / "emulation" / "roms"),
        "-hashpath", str(GYM_PATH / "emulation" / "hash"),
        "-state_directory", str(STATE_DIRECTORY),
        "-cfg_directory", str(GYM_PATH / ".mame"),
        "-skip_gameinfo",
        "-nonvram_save",
        "-sound", "none",
        "-window",
        "-console",
    ]
    if autosave:
        command.append("-autosave")
    return command


def _print_instructions(autosave):
    """Tell the player how to reach play and how to keep a state."""
    print(f"States land in: {STATE_DIRECTORY}")
    print("Press any key to leave the demo loop, then play to the situation you want.")
    print("At the console prompt in this terminal:")
    print('  manager.machine:save("name")   freezes this moment under that name')
    print('  manager.machine:load("name")   brings that moment back')
    print("MAME's own menu (Tab, then Save State) works too, but it saves into slots, not names.")
    if autosave:
        print("Saving on exit is also on: quitting writes auto.sta, which the next start restores.")
    print("Save from the dungeon or inventory view, not from a menu or the demo loop.")


def _print_states(before):
    """Report the states the session added, or what was already there."""
    after = _state_files()
    new_files = [path for path in after if path not in before]
    if new_files:
        print("\nState files this session wrote:")
        for path in new_files:
            print(f"  {path}")
    elif after:
        print("\nNo new state file; these were already on disk:")
        for path in after:
            print(f"  {path}")
    else:
        print("\nNo state files on disk — the session did not save one.")


def main():
    """Open MAME for a by-hand session and report what it saved."""
    autosave = AUTOSAVE_FLAG in sys.argv[1:]
    STATE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    before = _state_files()
    _print_instructions(autosave)
    # The console plugin writes its command history beside the process, so run
    # from the scratch directory rather than wherever this was launched.
    subprocess.run(
        _build_command(autosave), check=False, cwd=str(GYM_PATH / ".mame")
    )
    _print_states(before)
    return 0


if __name__ == "__main__":
    sys.exit(main())
