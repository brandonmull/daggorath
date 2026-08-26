"""Observation wrappers that adapt the environment to Stable-Baselines3.

The environment reports the perceived state as a six-channel Dict in its own
dtypes. One channel — the scalars — is uint16, which torch cannot ingest (torch
has no uint16 tensor type). Stable-Baselines3 therefore crashes on it before
the features extractor ever runs. This wrapper downcasts that channel to int32,
the torch-supported lossless width, and mirrors the change in the observation
space. It lives here, in the training repo, because it adapts the environment
to a specific trainer — the environment itself stays trainer-agnostic.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces

# The sole channel that needs a dtype change; every other channel is uint8,
# which torch accepts as-is.
_SCALARS_KEY = "scalars"


class CastScalarsWrapper(gym.ObservationWrapper):
    """Cast the observation's uint16 scalars to int32.

    The scalars are the nineteen always-present state fields. Their values
    (0-65535) fit int32 losslessly, so this is a pure widen-and-relabel — no
    normalization, no value change. The remaining channels pass through
    untouched.
    """

    def __init__(self, env: gym.Env) -> None:
        super().__init__(env)
        original_space = env.observation_space

        box = original_space[_SCALARS_KEY]
        new_spaces = dict(original_space.spaces)
        new_spaces[_SCALARS_KEY] = spaces.Box(
            low=box.low,
            high=box.high,
            shape=box.shape,
            dtype=np.int32,
        )
        self.observation_space = spaces.Dict(new_spaces)

    def observation(self, observation: dict) -> dict:
        observation = dict(observation)
        observation[_SCALARS_KEY] = observation[_SCALARS_KEY].astype(np.int32)
        return observation