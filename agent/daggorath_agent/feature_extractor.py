"""CNN + MLP feature extractor for the Dict observation.

The observation is a six-channel dict. One channel — the map — is spatial
(two planes: edge bytes and feature bytes), and the other five are flat arrays
of scalars and entity tables. This extractor routes the map through a small
convolutional network and the flat channels through a multi-layer perceptron,
then concatenates the two into one feature vector for the policy's linear
heads. This is the CNN + MLP split described in perception/plan.md.
"""

import math

import gymnasium as gym
import torch
from torch import nn

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor


# The spatial channel: two planes (edge bytes, feature bytes), channels-first.
_MAP_KEY = "map"

# The flat channels routed through the MLP, in a fixed order.
_VECTOR_KEYS = ("scalars", "hands", "pack", "creatures", "objects")


class DaggorathFeaturesExtractor(BaseFeaturesExtractor):
    """Routes the map through a CNN and the flat channels through an MLP.

    The map is the only spatial channel; the CNN reads local wall and feature
    structure from it. The remaining channels are flat, so an MLP reads them
    directly. The two branches are concatenated before the policy heads.
    """

    def __init__(
        self,
        observation_space: gym.spaces.Dict,
        features_dim: int = 256,
    ) -> None:
        super().__init__(observation_space, features_dim)

        map_space = observation_space[_MAP_KEY]
        in_channels = int(map_space.shape[0])

        # CNN over the two-plane map. Stride-2 convolutions downsample the map
        # (32x32 -> 16x16 -> 8x8) instead of pooling, so every shrink is a
        # learned transform; no information is discarded by a fixed summary.
        self._cnn = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Flatten(),
        )

        # MLP over the concatenated flat channels.
        vector_dim = sum(
            math.prod(observation_space[key].shape) for key in _VECTOR_KEYS
        )
        self._mlp = nn.Sequential(
            nn.Linear(vector_dim, 128),
            nn.ReLU(),
        )

        # Measure the CNN's output width from one synthetic sample so the final
        # projection's input width is exact rather than hand-computed.
        sample = torch.as_tensor(map_space.sample()).float().unsqueeze(0)
        cnn_dim = int(self._cnn(sample).shape[1])
        mlp_dim = 128

        self._combine = nn.Sequential(
            nn.Linear(cnn_dim + mlp_dim, features_dim),
            nn.ReLU(),
        )

    def forward(self, observations: dict[str, torch.Tensor]) -> torch.Tensor:
        """Concatenate the CNN's map features and the MLP's flat features."""
        map_features = self._cnn(observations[_MAP_KEY].float())

        vector_parts = [
            observations[key].float().flatten(start_dim=1)
            for key in _VECTOR_KEYS
        ]
        vector_features = self._mlp(torch.cat(vector_parts, dim=1))

        combined = torch.cat([map_features, vector_features], dim=1)
        return self._combine(combined)