"""Smoke tests for the SB3 training wiring — no MAME launch required.

Constructs the custom feature extractor and a PPO policy against the
environment's real observation/action spaces, then runs forward passes on a
synthetic observation to confirm shapes line up and a valid action comes out.
This exercises exactly what train() uses, minus the MAME subprocess (MAME only
starts on reset(), which these tests never call).
"""

import os
import sys
import tempfile

import torch

# Make daggorath_agent importable from source; daggorath_gym is installed
# editable and already on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.vec_env import DummyVecEnv  # noqa: E402

from daggorath_agent.feature_extractor import DaggorathFeaturesExtractor  # noqa: E402
from daggorath_agent.train import make_env  # noqa: E402


def test_extractor_output_shape():
    """The extractor emits (1, features_dim) for a sampled observation."""
    env = make_env()
    extractor = DaggorathFeaturesExtractor(env.observation_space)

    observation = env.observation_space.sample()
    tensor_obs = {
        key: torch.as_tensor(value).unsqueeze(0) for key, value in observation.items()
    }
    features = extractor(tensor_obs)

    assert tuple(features.shape) == (1, extractor.features_dim)


def test_ppo_policy_produces_valid_action():
    """A PPO policy with the custom extractor returns an in-range action."""
    env = make_env()
    vector_env = DummyVecEnv([make_env])

    model = PPO(
        "MultiInputPolicy",
        vector_env,
        policy_kwargs={"features_extractor_class": DaggorathFeaturesExtractor},
        seed=0,
    )

    observation = env.observation_space.sample()
    action, _ = model.predict(observation, deterministic=True)

    assert env.action_space.contains(action)


def test_checkpoint_roundtrip():
    """A saved model loads and predicts, honouring the load contract.

    Validates the two parts of the persist-learning decision's contract: that a
    saved checkpoint resolves the custom extractor by import path, and that a
    loaded model requires (and accepts) set_env() before predicting.
    """
    env = make_env()
    vector_env = DummyVecEnv([make_env])

    model = PPO(
        "MultiInputPolicy",
        vector_env,
        policy_kwargs={"features_extractor_class": DaggorathFeaturesExtractor},
        seed=0,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "model")
        model.save(path)

        loaded = PPO.load(path)
        loaded.set_env(DummyVecEnv([make_env]))

        observation = env.observation_space.sample()
        action, _ = loaded.predict(observation, deterministic=True)
        assert env.action_space.contains(action)
