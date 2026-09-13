"""Integration tests for the emulator's state channel — requires MAME.

MAME boots, the Lua producer samples RAM and writes tagged records to the
state FIFO, and MameOperator reads them back into DaggorathState. The
producer test reads the raw FIFO bytes; the reader and operator tests go
through recv().

Prerequisites:
    - MAME installed and on PATH
    - ROMs present at emulation/roms/
    - Hash files present at emulation/hash/
"""

import importlib
import os
import select
import struct
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force-reload to bypass stale editable-install cache
import daggorath_gym
importlib.reload(daggorath_gym)
from daggorath_gym.emulator import IpcConfig, MameConfig, MameOperator
from daggorath_gym.screen import PIXEL_BYTES
from daggorath_gym.state import (
    CREATURE_BYTES,
    CREATURE_FIELDS,
    CREATURE_SLOTS,
    FIELDS,
    FLOOR_OBJECT_CAPACITY,
    FLOOR_OBJECT_RAW_BYTES,
    FRAME_LEN,
    HAND_COUNT,
    HOLE_LADDER_CAPACITY,
    HOLE_LADDER_RAW_BYTES,
    HOLES_LADDERS_BYTES,
    MAP_SIZE,
    MAZE_BYTES,
    OBJECT_RAW_BYTES,
    OBJECTS_BYTES,
    PACK_CAPACITY,
    PERCEIVED_FIELDS,
    DaggorathState,
)

# Each test gets its own FIFO path to avoid collisions.
_IPC = IpcConfig(state_fifo_path="/tmp/daggorath-test-emulator", command_port=15101)

# Record sizes keyed by the one-byte tag — mirrors emulator._RECORD_LENGTHS so
# the producer test can read the raw wire without the reader.
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
    """The producer writes an F marker every frame, at ~60 Hz."""
    operator = MameOperator(
        mame_config=MameConfig(window=False, sound="none"),
        ipc_config=_IPC,
    )
    try:
        operator.start()

        # Wait for live play: the first record is the first F marker (the
        # keyboard prime lands at frame 300, a few seconds after boot).
        first = _read_raw_records(operator, 1, timeout=40.0)
        assert first and first[0][:1] == b"F", "no frame marker arrived"
        first_frame = struct.unpack("<I", first[0][1:5])[0]
        start_time = time.monotonic()

        # Collect a 10-second run so the frame rate can be measured.
        records = _read_raw_records(operator, 10_000, timeout=10.0)
        end_time = time.monotonic()
        records = first + records

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

        # The frame number advances at ~60 Hz over the 10-second run.
        hz = (frame_numbers[-1] - first_frame) / (end_time - start_time)
        assert 55.0 <= hz <= 65.0, f"frame rate {hz:.1f} Hz, expected ~60"
    finally:
        operator.stop()


def test_recv_returns_frame_number_and_state():
    """recv() returns (frame_number, state) with advancing frame numbers."""
    operator = MameOperator(
        mame_config=MameConfig(window=False, sound="none"),
        ipc_config=_IPC,
    )
    try:
        operator.start()
        frame_number, state = operator.recv()
        assert isinstance(frame_number, int)
        assert isinstance(state, DaggorathState)

        previous = frame_number
        for _ in range(20):
            frame_number, state = operator.recv()
            assert isinstance(frame_number, int)
            assert isinstance(state, DaggorathState)
            assert frame_number > previous
            previous = frame_number
    finally:
        operator.stop()


def test_operator_starts_and_stops():
    """MameOperator can start, receive a state frame, and stop cleanly."""
    operator = MameOperator(ipc_config=_IPC)
    try:
        operator.start()
        _, state = operator.recv()
        assert isinstance(state, DaggorathState)
    finally:
        operator.stop()


def test_state_has_valid_values():
    """Received state fields fall within sensible ranges for a booted game."""
    operator = MameOperator(ipc_config=_IPC)
    try:
        operator.start()
        _, state = operator.recv()

        # Game mode: demo (0xFF) or live (0x00) — both are valid at startup
        assert state.game_mode in (0x00, 0xFF)

        # Dungeon floor: 0–4 per the memory map
        assert 0 <= state.at_floor <= 4
    finally:
        operator.stop()


def test_state_as_perceived_shape():
    """as_perceived() produces a schema-consistent output from real MAME data."""
    operator = MameOperator(ipc_config=_IPC)
    try:
        operator.start()
        _, state = operator.recv()
        perceived = state.as_perceived()

        assert isinstance(perceived, dict)
        assert perceived["scalars"].dtype == np.uint16
        assert len(perceived["scalars"]) == len(PERCEIVED_FIELDS)
    finally:
        operator.stop()


def test_world_channels_arrive_and_decode():
    """M/C/O/H records arrive from MAME and decode into the true-state attributes."""
    operator = MameOperator(ipc_config=_IPC)
    try:
        operator.start()
        state = None
        for _ in range(50):
            _, state = operator.recv()
            if (
                state.maze is not None
                and state.creatures is not None
                and state.hands is not None
                and state.holes_ladders is not None
            ):
                break

        assert state is not None
        assert state.maze.shape == (MAP_SIZE, MAP_SIZE)
        assert state.creatures.shape == (CREATURE_SLOTS, CREATURE_FIELDS)
        assert state.hands.shape == (HAND_COUNT, OBJECT_RAW_BYTES)
        assert state.pack.shape == (PACK_CAPACITY, OBJECT_RAW_BYTES)
        assert state.objects.shape == (FLOOR_OBJECT_CAPACITY, FLOOR_OBJECT_RAW_BYTES)
        assert state.holes_ladders.shape == (2, HOLE_LADDER_CAPACITY, HOLE_LADDER_RAW_BYTES)
        # Every level has at least one real connection, so the decoded table
        # must not be all sentinel — a pointer-walk bug would empty it.
        assert np.any(state.holes_ladders[..., 0] != 0xFF)
    finally:
        operator.stop()
