#!/usr/bin/env python3
"""Launcher for the scripted machine save-load experiment.

Runs MAME with the sandbox plugin. In setup the plugin plays a scripted
situation and freezes it with machine:save; in verify it reports what a frozen
machine came back with. The plugin writes a report, and this launcher watches
that report for its closing line, then stops MAME.

Run: python gym/sandbox/machine-save-load/scripted/run.py setup <name>
     python gym/sandbox/machine-save-load/scripted/run.py verify <name>
"""

import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import (
    GYM_PATH,
    MACHINE_NAME,
    MAME_PLUGIN_PATH,
    SANDBOX_PATH,
    STATE_DIRECTORY,
)

PLUGIN_NAME = "scripted"
DONE_SENTINEL = "scripted: done"
REPORT_DIRECTORY = SANDBOX_PATH / "logs"

# The plugin lives in the sandbox folder's scripted subfolder, so the sandbox
# folder itself is the plugin path: -pluginspath names the directory that
# holds plugin folders, and the trailing entry is MAME's own plugins directory,
# without which boot.lua cannot be found.
PLUGIN_PATH = f"{SANDBOX_PATH};{MAME_PLUGIN_PATH}"

# Seconds to wait for the plugin's closing line.
TIMEOUTS = {"setup": 240, "verify": 60}


def _sibling_plugin_names():
    """Any other plugin sharing this path, which must not start.

    A plugin whose manifest says start begins whether or not -plugin names it,
    so anything else on the path has to be named to -noplugin.
    """
    return sorted(
        manifest.parent.name
        for manifest in SANDBOX_PATH.glob("*/plugin.json")
        if manifest.parent.name != PLUGIN_NAME
    )


def _build_command(mode, state_name):
    """Assemble the MAME command line for one run."""
    command = [
        "mame", MACHINE_NAME, "daggorath",
        "-rompath", str(GYM_PATH / "emulation" / "roms"),
        "-hashpath", str(GYM_PATH / "emulation" / "hash"),
        "-pluginspath", PLUGIN_PATH,
        "-plugin", PLUGIN_NAME,
        "-state_directory", str(STATE_DIRECTORY),
        "-cfg_directory", str(GYM_PATH / ".mame"),
        "-skip_gameinfo",
        "-nonvram_save",
        "-sound", "none",
    ]
    siblings = _sibling_plugin_names()
    if siblings:
        command.extend(["-noplugin", ",".join(siblings)])
    if mode == "verify":
        command.extend(["-state", state_name])
    return command


def _build_environment(mode, state_name, report_path):
    """The environment the plugin reads its instructions from."""
    environment = os.environ.copy()
    environment["SANDBOX_MODE"] = mode
    environment["SANDBOX_STATE_NAME"] = state_name
    environment["SANDBOX_STATE_DIRECTORY"] = str(STATE_DIRECTORY)
    environment["SANDBOX_REPORT_FILE"] = str(report_path)
    return environment


def _wait_for_report(report_path, timeout):
    """Wait for the plugin's closing line; return its text, or None."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if report_path.exists():
            for line in report_path.read_text().splitlines():
                if line.startswith(DONE_SENTINEL):
                    return line
        time.sleep(0.5)
    return None


def _stop(process):
    """Stop MAME once the plugin has finished its work."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    """Run one mode and report whether the plugin finished its work."""
    usage = [
        "Run: python gym/sandbox/machine-save-load/scripted/run.py setup <name>",
        "     python gym/sandbox/machine-save-load/scripted/run.py verify <name>",
    ]
    if len(sys.argv) != 3 or sys.argv[1] not in TIMEOUTS:
        print("\n".join(usage))
        return 2
    mode, state_name = sys.argv[1], sys.argv[2]

    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    STATE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIRECTORY / MACHINE_NAME / f"{state_name}.sta"
    if mode == "verify" and not state_path.exists():
        print(f"No state named {state_name!r} at {state_path}")
        available = sorted(path.stem for path in STATE_DIRECTORY.rglob("*.sta"))
        print("Available: " + (", ".join(available) if available else "(none)"))
        return 2

    report_path = REPORT_DIRECTORY / f"{mode}-{state_name}.txt"
    report_path.unlink(missing_ok=True)
    command = _build_command(mode, state_name)
    environment = _build_environment(mode, state_name, report_path)
    print(f"[run] {mode} {state_name}")
    process = subprocess.Popen(command, env=environment)
    closing = _wait_for_report(report_path, TIMEOUTS[mode])
    _stop(process)

    if report_path.exists():
        print(report_path.read_text(), end="")
    print(f"[run] report: {report_path}")
    if closing is None:
        print("[run] the plugin never finished")
        return 1
    if closing.endswith("ok"):
        if mode == "setup":
            print(f"[run] state: {state_path}")
        return 0
    print("[run] the plugin reported a failure")
    return 1


if __name__ == "__main__":
    sys.exit(main())
