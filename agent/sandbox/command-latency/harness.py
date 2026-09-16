"""Shared harness for the command-latency sandbox.

A session records every changed frame the game reports — one row per changed
frame, with the frame number, the still frames since the last change, the
true-state scalars, the command-area text, and the world channels — plus a row
for each command posted on the frame schedule. Nothing is interpreted while a
session runs.

Reading is a separate pass over the written trace. For each post, the analysis
finds the frame the echo appeared, the frame the parser matched, and the frame
a watched column changed, and reports the offsets. Which columns count as a
command's effect is part of that reading, not the recording, so the same trace
can be read again with a different field set.

A run is several sessions, each a fresh boot. The game's opening state is
deterministic, so the same schedule replays from the same situation and the
spread of the offsets is the variability.

Run through a child's ``run.py``; see ``README.md`` for the build order.
"""

import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_PROJECT_PATH = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_PROJECT_PATH / "gym"))

from daggorath_gym.commands import (
    NUM_OBJECT_SPECIFIERS,
    NUM_VERB_FORMS,
    DaggorathCommand,
    derive_command_index,
)
from daggorath_gym.emulator import MameOperator
from daggorath_gym.state import CREATURE_FIELDS, CREATURE_SLOTS, FIELDS

from frame_observation import FrameObservation

# Where the traces land; gitignored through the repository's ``logs/`` rule.
_LOG_DIRECTORY = Path(__file__).resolve().parent / "logs"

# Still frames recorded after the last post, so a slow effect has room to land.
_SETTLE_FRAMES = 200

# Log columns: the event tag, the frame number, the gap, every true-state
# scalar (so a schema extension is recorded without a change here), the
# command-area text, and the world channels the signal set names.
_SCALAR_NAMES = tuple(field_definition.name for field_definition in FIELDS)
_WORLD_NAMES = ("command_area_text", "hands", "pack", "lit_torch", "creatures")
_COLUMN_NAMES = ("event", "frame", "gap") + _SCALAR_NAMES + _WORLD_NAMES

# Creature-channel fields the reading can watch: per-slot values decoded from
# the C record. The offsets name the wire order alive, type, X, Y, damage,
# strength; damage and strength are two little-endian bytes.
_CREATURE_FIELD_OFFSETS = {
    "creature_alive": 0,
    "creature_damage": 4,
    "creature_strength": 6,
}
_CREATURE_FIELD_WIDTHS = {
    "creature_alive": 1,
    "creature_damage": 2,
    "creature_strength": 2,
}


@dataclass(frozen=True)
class ScheduleEntry:
    """One command posted at one frame of a session."""

    frame_number: int
    phrase: str


@dataclass(frozen=True)
class CommandLatency:
    """One post's offsets to each moment, read from a recorded trace."""

    phrase: str
    command_index: int
    post_frame: int
    written_offset: Optional[int]
    echo_cleared_offset: Optional[int]
    matched_offset: Optional[int]
    changed_offset: Optional[int]
    changes: dict = field(default_factory=dict)


# ---------- recording ----------

def _write_header(log_file) -> None:
    """Write the column names as the trace's first, comment-prefixed line."""
    log_file.write("#\t" + "\t".join(_COLUMN_NAMES) + "\n")


def _write_frame(log_file, frame_number: int, gap: int, state) -> None:
    """Write one changed frame's full signal row."""
    scalars = [str(getattr(state, field_name)) for field_name in _SCALAR_NAMES]
    command_area_text = state.command_area_text.replace("\n", "|")
    hands = _format_int_list(state.hands)
    pack = _format_int_list(state.pack)
    lit_torch = _format_int_list(state.lit_torch)
    if state.creatures is None:
        creatures = ""
    else:
        creatures = state.creatures.tobytes().hex()
    row = ["frame", str(frame_number), str(gap)]
    row.extend(scalars)
    row.extend([command_area_text, hands, pack, lit_torch, creatures])
    log_file.write("\t".join(row) + "\n")


def _write_post(log_file, frame_number: int, command_index: int, phrase: str) -> None:
    """Write one posted command's row."""
    log_file.write(f"post\t{frame_number}\t{command_index}\t{phrase}\n")


def _format_int_list(values) -> str:
    """Render a world-channel array as a pipe-joined list, empty when absent."""
    if values is None:
        return ""
    return "|".join(str(int(value)) for value in values.reshape(-1))


def _find_command_index(phrase: str) -> int:
    """Map a command phrase to its wire index through the public action space."""
    for verb_form in range(NUM_VERB_FORMS):
        for object_specifier in range(NUM_OBJECT_SPECIFIERS):
            command_index = derive_command_index(verb_form, object_specifier)
            if command_index is None:
                continue
            if DaggorathCommand(index=command_index).phrase == phrase:
                return command_index
    raise ValueError(f"No command index maps to phrase {phrase!r}")


# ---------- running ----------

def _advance_to_frame(observation, target_frame: int, log_file) -> None:
    """Record changes until the observation's frame reaches the target."""
    while observation.frame_number < target_frame:
        try:
            observation.advance_to_next_change()
        except TimeoutError:
            print("[harness] read timeout; ending the session early")
            break
        _write_frame(log_file, observation.frame_number, observation.gap, observation.state)


def run_session(operator, schedule, log_path, settle_frames=_SETTLE_FRAMES) -> None:
    """Post the schedule and record every change until the settle window ends."""
    observation = FrameObservation(operator)
    with open(log_path, "w") as log_file:
        _write_header(log_file)
        _write_frame(log_file, observation.frame_number, observation.gap, observation.state)
        for entry in schedule:
            _advance_to_frame(observation, entry.frame_number, log_file)
            command_index = _find_command_index(entry.phrase)
            _write_post(log_file, observation.frame_number, command_index, entry.phrase)
            operator.send(DaggorathCommand(index=command_index))
        _advance_to_frame(
            observation, schedule[-1].frame_number + settle_frames, log_file
        )


def run_sessions(
    schedule,
    watched_fields,
    session_count,
    experiment_name,
    mame_config,
    ipc_config,
    settle_frames=_SETTLE_FRAMES,
    log_directory=None,
) -> list:
    """Record several fresh sessions, then read the traces and report them."""
    if log_directory is None:
        log_directory = _LOG_DIRECTORY
    log_directory.mkdir(parents=True, exist_ok=True)

    log_paths = []
    for index in range(session_count):
        log_path = log_directory / f"{experiment_name}-{index:02d}.log"
        operator = MameOperator(mame_config=mame_config, ipc_config=ipc_config)
        print(f"[harness] session {index}: booting MAME")
        operator.start()
        try:
            run_session(operator, schedule, log_path, settle_frames)
            print(f"[harness] session {index}: {log_path}")
        except Exception as error:
            print(f"[harness] session {index} failed: {error}")
        finally:
            operator.stop()
        log_paths.append(log_path)

    per_session = [
        analyze_trace(log_path, watched_fields)
        for log_path in log_paths
        if log_path.exists()
    ]
    print_reports(per_session)
    return per_session


# ---------- reading ----------

def _parse_trace(log_path):
    """Read a trace into its changed-frame rows and its posted commands."""
    frames = []
    posts = []
    for line in log_path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[0] == "post":
            posts.append((int(parts[1]), int(parts[2]), parts[3]))
            continue
        if parts[0] != "frame":
            continue
        frame = {"frame": int(parts[1]), "gap": int(parts[2]), "scalars": {}}
        cursor = 3
        for field_name in _SCALAR_NAMES:
            frame["scalars"][field_name] = int(parts[cursor])
            cursor += 1
        frame["command_area_text"] = parts[cursor]
        cursor += 1
        frame["hands"] = _parse_int_list(parts[cursor])
        cursor += 1
        frame["pack"] = _parse_int_list(parts[cursor])
        cursor += 1
        frame["lit_torch"] = _parse_int_list(parts[cursor])
        cursor += 1
        frame["creatures"] = bytes.fromhex(parts[cursor]) if parts[cursor] else b""
        frames.append(frame)
    return frames, posts


def _parse_int_list(value: str) -> list:
    """Parse a pipe-joined world-channel value, empty when absent."""
    if not value:
        return []
    return [int(token) for token in value.split("|")]


def _field_value(frame, name: str):
    """Read one watched column from a parsed frame.

    Scalar fields and world-channel columns carry their recorded value; the
    creature per-slot fields are decoded from the C channel's bytes.
    """
    if name in _CREATURE_FIELD_OFFSETS:
        return _creature_field_values(frame, name)
    if name in frame["scalars"]:
        return frame["scalars"][name]
    return frame[name]


def _creature_field_values(frame, name):
    """Decode one creature field for every slot from the C channel's bytes."""
    creatures = frame.get("creatures", b"")
    if not creatures:
        return None
    offset = _CREATURE_FIELD_OFFSETS[name]
    width = _CREATURE_FIELD_WIDTHS[name]
    values = []
    for slot in range(CREATURE_SLOTS):
        base = slot * CREATURE_FIELDS + offset
        value = creatures[base]
        if width == 2:
            value += creatures[base + 1] << 8
        values.append(value)
    return tuple(values)


def _baseline_frame(frames, post_frame: int):
    """The last recorded frame at or before the post."""
    baseline = None
    for frame in frames:
        if frame["frame"] > post_frame:
            break
        baseline = frame
    return baseline


def _offset(post_frame: int, frame) -> Optional[int]:
    """The post-to-frame distance, or None when the moment never arrived."""
    if frame is None:
        return None
    return frame["frame"] - post_frame


def _first_frame(window, predicate):
    """The first frame in the window that satisfies the predicate."""
    for frame in window:
        if predicate(frame):
            return frame
    return None


def _changed_fields(baseline, frame, watched_fields) -> dict:
    """The watched columns that differ between the baseline and this frame."""
    changes = {}
    for name in watched_fields:
        before = _field_value(baseline, name)
        after = _field_value(frame, name)
        if before is None or after is None:
            continue
        if before != after:
            changes[name] = (before, after)
    return changes


def _first_match_edge(window, initial_value):
    """The first 0 -> non-zero rising edge of command_parser_word_count in the window.

    command_parser_word_count resets to 0 once the word table is exhausted, so
    every match starts with a fresh 0 -> N edge. command_parser_matched_exactly
    latches and stays 0xFF across matches, so it cannot mark the later ones.
    """
    previous = initial_value
    for frame in window:
        value = frame["scalars"]["command_parser_word_count"]
        if previous == 0 and value != 0:
            return frame
        previous = value
    return None


def analyze_trace(log_path, watched_fields) -> list:
    """Read one trace into a per-post latency record for each command posted."""
    frames, posts = _parse_trace(log_path)
    latencies = []
    for index, (post_frame, command_index, phrase) in enumerate(posts):
        if index + 1 < len(posts):
            next_post_frame = posts[index + 1][0]
        else:
            next_post_frame = None
        window = [
            frame
            for frame in frames
            if frame["frame"] > post_frame
            and (next_post_frame is None or frame["frame"] < next_post_frame)
        ]
        baseline = _baseline_frame(frames, post_frame)
        if baseline is None:
            baseline_text = ""
            baseline_words = 0
        else:
            baseline_text = baseline["command_area_text"]
            baseline_words = baseline["scalars"]["command_parser_word_count"]

        written_frame = _first_frame(
            window, lambda frame: frame["command_area_text"] != baseline_text
        )
        echo_cleared_frame = None
        if written_frame is not None:
            after_written = [
                frame for frame in window if frame["frame"] > written_frame["frame"]
            ]
            echo_cleared_frame = _first_frame(
                after_written, lambda frame: frame["command_area_text"] == baseline_text
            )

        matched_frame = _first_match_edge(window, baseline_words)

        changed_frame = None
        changes = {}
        if baseline is not None:
            watched = watched_fields.get(phrase, ())
            for frame in window:
                frame_changes = _changed_fields(baseline, frame, watched)
                if frame_changes:
                    changed_frame = frame
                    changes = frame_changes
                    break

        latencies.append(
            CommandLatency(
                phrase=phrase,
                command_index=command_index,
                post_frame=post_frame,
                written_offset=_offset(post_frame, written_frame),
                echo_cleared_offset=_offset(post_frame, echo_cleared_frame),
                matched_offset=_offset(post_frame, matched_frame),
                changed_offset=_offset(post_frame, changed_frame),
                changes=changes,
            )
        )
    return latencies


# ---------- reporting ----------

def _format_offset(offset: Optional[int]) -> str:
    """Render a frame offset for the report."""
    if offset is None:
        return "--"
    return f"+{offset}"


def _format_value(value) -> str:
    """Render a watched column's value for the report."""
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if isinstance(value, bytes):
        return f"{len(value)} bytes"
    return str(value)


def _format_change(change) -> str:
    """Render one watched column's before/after for the report.

    Per-slot creature fields print only the slots that changed, not the whole
    32-slot tuple.
    """
    before, after = change
    if isinstance(before, tuple) and isinstance(after, tuple):
        changed_slots = [
            f"slot {index}: {before[index]} -> {after[index]}"
            for index in range(len(before))
            if before[index] != after[index]
        ]
        return ", ".join(changed_slots)
    return f"{_format_value(before)} -> {_format_value(after)}"


def _describe(values: list) -> str:
    """Render the spread of one offset across a set of results."""
    if not values:
        return "none"
    return (
        f"{min(values)}..{max(values)} "
        f"(mean {statistics.mean(values):.1f}, n={len(values)})"
    )


def print_reports(per_session) -> None:
    """Print each session's per-post offsets, then the cross-session spread."""
    for index, latencies in enumerate(per_session):
        print(f"\nsession {index}")
        for latency in latencies:
            columns = [
                f"post {latency.post_frame:>6}",
                f"{latency.phrase:<18}",
                f"written {_format_offset(latency.written_offset):>4}",
                f"echo-cleared {_format_offset(latency.echo_cleared_offset):>4}",
                f"matched {_format_offset(latency.matched_offset):>4}",
                f"changed {_format_offset(latency.changed_offset):>4}",
            ]
            print("  " + "  ".join(columns))
            for name in sorted(latency.changes):
                print(f"      {name}: {_format_change(latency.changes[name])}")

    phrases = []
    for latencies in per_session:
        for latency in latencies:
            if latency.phrase not in phrases:
                phrases.append(latency.phrase)

    print("\nlatency across sessions")
    for phrase in phrases:
        written = [
            latency.written_offset
            for latencies in per_session
            for latency in latencies
            if latency.phrase == phrase and latency.written_offset is not None
        ]
        matched = [
            latency.matched_offset
            for latencies in per_session
            for latency in latencies
            if latency.phrase == phrase and latency.matched_offset is not None
        ]
        changed = [
            latency.changed_offset
            for latencies in per_session
            for latency in latencies
            if latency.phrase == phrase and latency.changed_offset is not None
        ]
        print(
            f"  {phrase:<18} written {_describe(written)}  "
            f"matched {_describe(matched)}  changed {_describe(changed)}"
        )
