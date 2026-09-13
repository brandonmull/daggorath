#!/usr/bin/env python3
"""Launch MAME with the state-field-verification plugin and check its log.

The plugin pokes known values into RAM; the production state sampler writes
tagged records to a log file. This script decodes those records with the
production deserializer and asserts the poked values round-trip correctly.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

DURATION = 30
PIXEL_BYTES = 1024

script_dir = Path(__file__).resolve().parent
sandbox_dir = script_dir.parent
project_root = sandbox_dir.parent
rom_path = project_root / "emulation" / "roms"
hash_path = project_root / "emulation" / "hash"
plugins_path = project_root / "emulation" / "plugins"
scratch_dir = project_root / ".mame"
log_file = script_dir / "log.txt"

scratch_dir.mkdir(exist_ok=True)

mame_cmd = [
    "mame", "coco3", "daggorath",
    "-rompath", str(rom_path),
    "-hashpath", str(hash_path),
    "-pluginspath", f"{sandbox_dir};/usr/local/share/games/mame/plugins",
    "-plugin", "state-field-verification",
    "-cfg_directory", str(scratch_dir),
    "-skip_gameinfo",
    "-nonvram_save",
    "-window",
    "-sound", "none",
]

env = os.environ.copy()
env["LOG_FILE"] = str(log_file)
env["DAGGORATH_PLUGINS_DIR"] = str(plugins_path)

print("Launching MAME...", file=sys.stderr)
mame_process = subprocess.Popen(
    mame_cmd,
    cwd=str(project_root / "emulation"),
    env=env,
    stdout=None,
    stderr=None,
)

print(f"Waiting {DURATION}s...", file=sys.stderr)
time.sleep(DURATION)

if mame_process.poll() is None:
    print("Terminating MAME...", file=sys.stderr)
    mame_process.terminate()
    try:
        mame_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        mame_process.kill()
        mame_process.wait()

# ---- analysis -------------------------------------------------------------

sys.path.insert(0, str(project_root))
from daggorath_gym.state import (
    CREATURE_BYTES,
    FRAME_LEN,
    HOLES_LADDERS_BYTES,
    MAZE_BYTES,
    OBJECTS_BYTES,
    DaggorathState,
)

RECORD_LENGTHS = {
    ord("S"): 1 + FRAME_LEN,
    ord("T"): 1 + 1 + PIXEL_BYTES,
    ord("B"): 1 + FRAME_LEN + 1 + PIXEL_BYTES,
    ord("M"): 1 + MAZE_BYTES,
    ord("C"): 1 + CREATURE_BYTES,
    ord("O"): 1 + OBJECTS_BYTES,
    ord("H"): 1 + HOLES_LADDERS_BYTES,
}

# Scalar fields verified by attribute name.
EXPECTED_SCALARS = {
    "ambient_light_physical": 0x01,
    "ambient_light_magical": 0x02,
    "m0221": 0x000A,
}

# Lit-torch entry verified by index: class, proper, reveal, minutes, physical
# light, magic light. Only the special data is poked, so only it is checked.
EXPECTED_TORCH = {
    3: 100,  # minutes
    4: 7,    # physical light
    5: 3,    # magic light
}


def decode_records(data):
    """Reconstruct a DaggorathState per record, carrying the latest frame and object record."""
    records = []
    frame = None
    objects = None
    i = 0
    while i < len(data):
        tag = data[i]
        length = RECORD_LENGTHS.get(tag)
        if length is None or i + length > len(data):
            break
        record = data[i:i + length]
        if tag in (ord("S"), ord("B")):
            frame = record[1:1 + FRAME_LEN]
        elif tag == ord("O"):
            objects = record[1:1 + OBJECTS_BYTES]
        if frame is not None:
            records.append(DaggorathState(frame, objects=objects))
        i += length
    return records


def main():
    if not log_file.exists():
        print(f"FAIL: no log file at {log_file}", file=sys.stderr)
        return 1

    records = decode_records(log_file.read_bytes())
    print(f"Decoded {len(records)} state records", file=sys.stderr)

    observed_scalars = {name: set() for name in EXPECTED_SCALARS}
    observed_torch = {index: set() for index in EXPECTED_TORCH}
    for state in records:
        for name in EXPECTED_SCALARS:
            observed_scalars[name].add(getattr(state, name))
        if state.lit_torch is not None:
            for index in EXPECTED_TORCH:
                observed_torch[index].add(int(state.lit_torch[index]))

    failures = []
    for name, want in EXPECTED_SCALARS.items():
        if want in observed_scalars[name]:
            print(f"PASS  {name} == {want}")
        else:
            preview = sorted(observed_scalars[name])[:8]
            print(f"FAIL  {name}: expected {want}, saw {preview}...")
            failures.append(name)
    for index, want in EXPECTED_TORCH.items():
        if want in observed_torch[index]:
            print(f"PASS  lit_torch[{index}] == {want}")
        else:
            preview = sorted(observed_torch[index])[:8]
            print(f"FAIL  lit_torch[{index}]: expected {want}, saw {preview}...")
            failures.append(f"lit_torch[{index}]")

    if failures:
        print(f"\nRESULT: FAIL ({len(failures)} field(s) not observed)")
        return 1
    print("\nRESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
