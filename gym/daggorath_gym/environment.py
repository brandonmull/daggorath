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
    frame numbers under info["frames"].
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
        # command is sent, and the frame still advances.
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
            # A no-op action sends nothing; advance one change as before.
            state = self._receive_latest_state()
            changes = []
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
        """Block until a change arrives and return the latest state."""
        while True:
            changes = self._emulator.recv()
            if changes:
                return changes[-1][1]

    def _receive_until_settled(self) -> list[tuple[int, DaggorathState]]:
        """Receive changes until the posted command has finished.

        command_parser_position leaves its idle value while the game types and
        runs a command, and returns once the handler has finished. Collects
        every changed frame along the way and returns the full list, in order,
        ending at the settled state. Stops early when the game ends, and falls
        back to the changes seen so far after _SETTLE_FRAME_LIMIT frames so a
        lost command cannot hang the step.
        """
        changes: list[tuple[int, DaggorathState]] = []
        saw_busy = False
        first_frame = None
        while True:
            for frame_number, state in self._emulator.recv():
                changes.append((frame_number, state))
                if first_frame is None:
                    first_frame = frame_number
                if self._check_terminated(state):
                    return changes
                if state.command_parser_position != _IDLE_PARSE_POSITION:
                    saw_busy = True
                elif saw_busy:
                    return changes
            if (
                first_frame is not None
                and changes[-1][0] - first_frame >= _SETTLE_FRAME_LIMIT
            ):
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
