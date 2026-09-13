"""Integration test for the frame-reporting producer — requires MAME.

Reads the raw state FIFO bytes the Lua sampler writes and verifies the
frame-reporting wire format: every frame emits an F marker with a 4-byte
little-endian frame number, the numbers advance, empty frames appear as a
marker alone, and content records sit only between markers.

Prerequisites: MAME installed and on PATH, ROMs/hash present (see test_emulator.py).
"""

import importlib
import os
import select
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force-reload to bypass stale editable-install cache
import daggorath_gym
importlib.reload(daggorath_gym)
from daggorath_gym.emulator import IpcConfig, MameConfig, MameOperator
from daggorath_gym.screen import PIXEL_BYTES
from daggorath_gym.state import (
    CREATURE_BYTES,
    FRAME_LEN,
    HOLES_LADDERS_BYTES,
    MAZE_BYTES,
    OBJECTS_BYTES,
)

# Each test gets its own FIFO path to avoid collisions.
_IPC = IpcConfig(state_fifo_path="/tmp/daggorath-test-frame-reporting", command_port=15301)

# Record sizes keyed by the one-byte tag — mirrors emulator._RECORD_LENGTHS so
# the test reads the raw wire without the reader.
_RECORD_LENGTHS = {
    b"F": 5,
    b"S": 1 + FRAME_LEN,
    b"T": 1 + 1 + PIXEL_BYTES,
    b"B": 1 + FRAME_LEN + 1 + PIXEL_BYTES,
    b"M": 1 + MAZE_BYTES,
    b"C": 1 + CREATURE_BYTES,
    b"O": 1 + OBJECTS_BYTES,
    b"H": 1 + HOLES_LADDERS_BYTES,
}

_CONTENT_TAGS = (b"S", b"B", b"T", b"M", b"C", b"O", b"H")


def _read_raw_records(operator, count, timeout):
    """Read up to `count` complete records from the producer's FIFO.

    Reads the FIFO directly — not through `recv` — so the test sees the
    producer's raw bytes, empty frames included.
    """
    records = []
    buffer = b""
    deadline = time.monotonic() + timeout
    while len(records) < count:
        tag = buffer[:1]
        length = _RECORD_LENGTHS.get(tag)
        if length is not None and len(buffer) >= length:
            records.append(buffer[:length])
            buffer = buffer[length:]
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        readable, _, _ = select.select([operator._state_fd], [], [], remaining)
        if not readable:
            break
        try:
            chunk = os.read(operator._state_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        buffer += chunk
    return records


def test_producer_reports_every_frame():
    """The producer writes an F marker every frame, empty frames included."""
    operator = MameOperator(
        mame_config=MameConfig(window=False, sound="none"),
        ipc_config=_IPC,
    )
    try:
        operator.start()

        # The keyboard prime lands at frame 300, so the first marker follows a
        # few seconds later; drain until a few hundred records have arrived.
        records = _read_raw_records(operator, 400, timeout=40.0)
        assert len(records) >= 2, "no records arrived from the producer"

        # The stream starts with a frame marker, never content.
        assert records[0][:1] == b"F"

        frame_numbers = []
        saw_content = False
        for record in records:
            if record[:1] == b"F":
                frame_numbers.append(struct.unpack("<I", record[1:5])[0])
            else:
                assert record[:1] in _CONTENT_TAGS
                saw_content = True

        # Frame numbers advance, and are sane (little-endian, not byte-swapped).
        assert len(frame_numbers) >= 2
        assert all(a < b for a, b in zip(frame_numbers, frame_numbers[1:]))
        assert all(0 < n < 10_000_000 for n in frame_numbers)

        # The heartbeat: at least one empty frame (a marker followed directly
        # by the next marker, with no content in between).
        assert any(
            records[i][:1] == b"F" and records[i + 1][:1] == b"F"
            for i in range(len(records) - 1)
        ), "no empty frame (marker alone) appeared"

        # Content also flowed, so the marker is not the only thing written.
        assert saw_content
    finally:
        operator.stop()
