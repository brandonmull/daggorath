"""Training entry point — the reference end-to-end PPO trainer.

Assembles the pipeline the deployment decision describes:

    train()
        -> constructs the environment (headless by default, windowed via --watch)
        -> applies the reward wrapper
        -> wraps it in a vector environment
        -> trains PPO
        -> saves checkpoints

The observation's uint16 scalars are widened to int32 at the outermost layer
so torch can ingest them (see wrappers.py); the environment itself is
unchanged, and the environment package imports no training library.

"Watch training" is the windowed mode: run with --watch to see the agent act
in the MAME window as it learns (see docs/plans/watch-training.md).
"""

import argparse
import os

import gymnasium as gym

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv

from daggorath_gym.emulator import MameConfig
from daggorath_gym.environment import DaggorathEnv
from daggorath_gym.reward import DaggorathRewardWrapper

from .feature_extractor import DaggorathFeaturesExtractor
from .wrappers import CastScalarsWrapper

# Checkpoints land in the repo's own checkpoints/ directory (gitignored),
# resolved relative to this file so the location is stable regardless of the
# working directory the command is run from.
_REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CHECKPOINT_DIR = os.path.join(_REPO_PATH, "checkpoints")
_FINAL_MODEL_PATH = os.path.join(_CHECKPOINT_DIR, "ppo-daggorath")

_DEFAULT_CHECKPOINT_FREQ = 10_000


def make_env(window: bool = False, sound: str = "none") -> gym.Env:
    """Build the reward-wrapped environment for one vector slot.

    Args:
        window: True shows the MAME window (watch training).
        sound: MAME sound setting ("sdl" for audio, "none" for silent).
    """
    env = DaggorathEnv(mame_config=MameConfig(window=window, sound=sound))
    env = DaggorathRewardWrapper(env)
    env = CastScalarsWrapper(env)
    return env


def train(
    total_timesteps: int = 100_000,
    seed: int | None = None,
    window: bool = False,
    sound: str = "none",
    checkpoint_freq: int = _DEFAULT_CHECKPOINT_FREQ,
    resume: str | None = None,
) -> PPO:
    """The reference train() pipeline: env -> reward -> VecEnv -> PPO.

    Args:
        total_timesteps: Number of environment steps to train for.
        seed: Optional random seed passed to PPO (ignored when resuming).
        window: True shows the MAME window while training.
        sound: MAME sound setting ("sdl" or "none").
        checkpoint_freq: Steps between periodic checkpoint saves.
        resume: Path to a saved checkpoint to continue training from. When
            omitted, the model starts from fresh random initialization.

    Returns:
        The trained PPO model.
    """
    vector_env = DummyVecEnv([lambda: make_env(window=window, sound=sound)])

    if resume is not None:
        # A loaded model carries weights but no environment; reattach it before
        # learning or predicting (the persist-learning plan's load contract).
        model = PPO.load(resume)
        model.set_env(vector_env)
    else:
        model = PPO(
            "MultiInputPolicy",
            vector_env,
            policy_kwargs={
                "features_extractor_class": DaggorathFeaturesExtractor,
            },
            seed=seed,
            verbose=1,
        )

    os.makedirs(_CHECKPOINT_DIR, exist_ok=True)
    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=_CHECKPOINT_DIR,
        name_prefix="ppo-daggorath",
    )
    # reset_num_timesteps=False only when resuming: that preserves the step
    # counter and learning-rate schedule — "continue", not "restart". A fresh
    # model uses the default (True).
    model.learn(
        total_timesteps=total_timesteps,
        callback=checkpoint_callback,
        reset_num_timesteps=(resume is None),
    )

    model.save(_FINAL_MODEL_PATH)
    return model


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a PPO agent on Daggorath.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Show the MAME window and enable sound (watch training).",
    )
    parser.add_argument(
        "--sound",
        choices=("sdl", "none"),
        default=None,
        help="MAME sound setting; with --watch defaults to sdl, else none.",
    )
    parser.add_argument(
        "--total-timesteps",
        type=int,
        default=100_000,
        help="Number of environment steps to train for.",
    )
    parser.add_argument(
        "--checkpoint-freq",
        type=int,
        default=_DEFAULT_CHECKPOINT_FREQ,
        help="Steps between periodic checkpoint saves.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for PPO.",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Path to a saved checkpoint to continue training from.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    window = args.watch
    sound = args.sound if args.sound is not None else ("sdl" if args.watch else "none")
    train(
        total_timesteps=args.total_timesteps,
        seed=args.seed,
        window=window,
        sound=sound,
        checkpoint_freq=args.checkpoint_freq,
        resume=args.resume,
    )
