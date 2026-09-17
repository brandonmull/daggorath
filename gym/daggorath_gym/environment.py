"""Gymnasium environment for Dungeons of Daggorath (1982) on MAME."""

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from .emulator import MameOperator, IpcConfig
from .commands import (
    NUM_OBJECT_SPECIFIERS,
    NUM_VERB_FORMS,
    DaggorathCommand,
    derive_command_index,
)
from .state import PERCEIVED_SPACE, DaggorathState


# The parser's position at rest — the start of the input line. It leaves this
# value while a command is typed and run, and returns once the handler has
# finished.
_IDLE_PARSE_POSITION = 0x02F1

# Frames to wait for a command to finish before giving up. Typing is about ten
# frames per character and the longest command is about fifteen characters, so
# 600 frames leaves ample margin without risking a hung step.
_SETTLE_FRAME_LIMIT = 600

# Frames a no-op step waits: one second of game time at 60 Hz. The window is
# the inaction baseline the attribution work reads.
_WAIT_FRAMES = 60


def _perceived_equal(a: dict, b: dict) -> bool:
    """True when two perceived observations carry the same channel values."""
    for key in a:
        if not np.array_equal(a[key], b[key]):
            return False
    return True


def _dedupe_perceived(
    changes: list[tuple[int, DaggorathState]],
    baseline: dict | None = None,
) -> tuple[list[dict], list[int]]:
    """Collapse a change set to its distinct perceived states.

    Consecutive changes whose perceived state is identical (the echo frames,
    which alter nothing the player sees) collapse to one entry, keeping the
    first frame at which each perceived state appeared. Changes identical to
    the baseline are dropped too, so the list starts at the first real change.
    """
    perceived_changes = []
    frames = []
    previous = baseline
    for frame_number, state in changes:
        perceived = state.as_perceived()
        if previous is None or not _perceived_equal(previous, perceived):
            perceived_changes.append(perceived)
            frames.append(frame_number)
            previous = perceived
    return perceived_changes, frames


class DaggorathEnv(gym.Env):
    """A Gymnasium environment that wraps Dungeons of Daggorath via MAME.

    Action space: MultiDiscrete([26, 31]) — a (verb form, object specifier) pair.
    Observation space: Dict — the perceived state (scalars + world channels).
    Lifecycle: owns a MameOperator; creates it on reset(), stops on close().
    step() waits for a posted command to finish, so one step spans one command,
    and returns the distinct perceived changes under info["changes"] plus their
    frame numbers under info["frames"]. A no-op step waits one second and
    returns the world's own changes over that window.
    Status: reward is a placeholder 0.0 (the reward wrapper computes the real
    value); termination is detected (death and the win); truncation is delegated
    to TimeLimit.
    """

    def __init__(self, mame_config=None, ipc_config=None):
        super(DaggorathEnv, self).__init__()

        self._mame_config = mame_config
        self._ipc_config = ipc_config

        # Action space: (verb form, object specifier) — the command shape plus the object
        # specifier index shared with the observation.
        self.action_space = spaces.MultiDiscrete([NUM_VERB_FORMS, NUM_OBJECT_SPECIFIERS])

        # Observation space: the perceived state (scalars + gated world channels)
        self.observation_space = PERCEIVED_SPACE

        self._emulator: MameOperator | None = None

        # The most recent true (ungated) state. The environment holds it so
        # the reward wrapper can read it through the environment object —
        # never through `info` or the observation (see agent/docs/3_decisions/reward.md).
        self._current_state: DaggorathState | None = None

    # ---- Gym interface ---------------------------------------------------

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        """Start a new episode.

        Args:
            seed: Random seed (not yet wired to an RNG).
            options: Optional configuration dict (not yet used).

        Returns:
            (observation, info) tuple. Info contains {"seed": seed}
            when seed is provided.
        """
        if self._emulator is not None:
            self._emulator.stop()

        self._emulator = MameOperator(
            mame_config=self._mame_config,
            ipc_config=self._ipc_config,
        )
        self._emulator.start()

        state = self._receive_latest_state()
        self._current_state = state

        info: dict = {}
        if seed is not None:
            info["seed"] = seed

        return state.as_perceived(), info

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict]:
        # Map the factored action to a wire command index. A syntactically
        # invalid pair (INCANT + non-ring) yields None and is a no-op — no
        # command is sent, and the step waits the fixed no-action window.
        command_index = derive_command_index(int(action[0]), int(action[1]))
        baseline = (
            self._current_state.as_perceived() if self._current_state is not None else None
        )
        if command_index is not None:
            self._emulator.send(DaggorathCommand(index=command_index))
            # Wait for the command to finish, so one step spans one command.
            # The distinct perceived changes ride in info for causal attribution.
            changes = self._receive_until_settled()
            state = changes[-1][1]
        else:
            # A no-op action sends nothing; wait the fixed window and report
            # the world's own motion.
            changes = self._receive_for_window(_WAIT_FRAMES)
            state = changes[-1][1]
        self._current_state = state

        perceived_changes, frames = _dedupe_perceived(changes, baseline)

        reward = self._compute_reward(state)
        terminated = self._check_terminated(state)
        truncated = self._check_truncated(state)

        observation = (
            perceived_changes[-1] if perceived_changes else state.as_perceived()
        )
        info = {"changes": perceived_changes, "frames": frames}

        return observation, reward, terminated, truncated, info

    def close(self):
        if self._emulator is not None:
            self._emulator.stop()
            self._emulator = None

    # ---- helpers ---------------------------------------------------------

    @property
    def current_state(self) -> DaggorathState | None:
        """The most recent true (ungated) state, for the reward wrapper."""
        return self._current_state

    def _receive_latest_state(self) -> DaggorathState:
        """Block until a frame arrives and return the latest state."""
        while True:
            changes = self._emulator.recv()
            if changes:
                return changes[-1][1]

    def _receive_until_settled(self) -> list[tuple[int, DaggorathState]]:
        """Receive frames until the posted command has finished.

        command_parser_position leaves idle when the game starts typing and
        returns when the handler has finished. Frames before that departure
        are dropped, so the returned list starts at the command and ends at
        the settled frame. Stops early when the game ends, and gives up after
        _SETTLE_FRAME_LIMIT frames.
        """
        changes: list[tuple[int, DaggorathState]] = []
        command_started = False
        command_start_frame = None
        discarded = 0
        while True:
            for frame_number, state in self._emulator.recv():
                if state.command_parser_position != _IDLE_PARSE_POSITION:
                    if not command_started:
                        command_started = True
                        command_start_frame = frame_number
                if command_started:
                    changes.append((frame_number, state))
                else:
                    discarded += 1
                if self._check_terminated(state):
                    return changes
                if (
                    command_started
                    and state.command_parser_position == _IDLE_PARSE_POSITION
                ):
                    return changes
            if (
                command_start_frame is not None
                and changes
                and changes[-1][0] - command_start_frame >= _SETTLE_FRAME_LIMIT
            ):
                return changes
            if not command_started and discarded >= _SETTLE_FRAME_LIMIT:
                return changes

    def _receive_for_window(
        self, frame_limit: int
    ) -> list[tuple[int, DaggorathState]]:
        """Collect frame_limit frames of the world's own motion.

        Drains the backlog to learn the current frame, then collects fresh
        frames until frame_limit have passed. Stops early when the game ends.
        """
        changes: list[tuple[int, DaggorathState]] = []
        anchor = None
        while True:
            batch = self._emulator.recv()
            if not batch:
                continue
            if anchor is None:
                anchor = batch[-1][0]
                continue
            for frame_number, state in batch:
                changes.append((frame_number, state))
                if self._check_terminated(state):
                    return changes
                if frame_number - anchor >= frame_limit:
                    return changes

    def _compute_reward(self, state) -> float:
        # The environment returns a placeholder reward; the agent-side reward
        # wrapper (reward.py) reads true state and computes the real scalar.
        return 0.0

    def _check_terminated(self, state) -> bool:
        # Death or the win. Death has two signals (belt-and-suspenders):
        # game_mode flips 0x00 -> 0xFF, and player_strength < m0221 is the
        # game's own death condition. The win is two-stage: holding the FINAL
        # ring (0x12) after INCANT FINAL — the wizard kill is NOT terminal.
        return (
            state.game_mode == 0xFF
            or state.player_strength < state.m0221
            or state.holds_final_ring
        )

    def _check_truncated(self, state) -> bool:
        # No built-in time limit; truncation is gymnasium's TimeLimit wrapper,
        # applied externally. The environment itself never truncates.
        return False
