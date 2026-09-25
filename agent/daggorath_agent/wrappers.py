"""Agent-side wrappers over the environment's observation.

CastScalarsWrapper widens the uint16 scalars to int32, since torch has no
uint16 tensor type and Stable-Baselines3 crashes on them before the feature
extractor runs. PerceivedObjectsWrapper translates the raw object channels
into the agent's object schema, the modifiable default. Both live in the agent
package because they adapt the environment to the agent, never the reverse.
"""

from dataclasses import dataclass

import numpy as np
import gymnasium as gym
from gymnasium import spaces

# The sole channel that needs a dtype change; every other channel is uint8,
# which torch accepts as-is.
_SCALARS_KEY = "scalars"


class CastScalarsWrapper(gym.ObservationWrapper):
    """Cast the observation's uint16 scalars to int32.

    The scalars are the fourteen perceived state fields. Their values
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


# ---- perceived object schema ---------------------------------------------

# The six object classes, in the specifier-index order the environment ships.
_OBJECT_CLASSES = ["FLASK", "RING", "SCROLL", "SHIELD", "SWORD", "TORCH"]

# The proper names per class, class-major, matching the specifier ordering.
_OBJECT_PROPER_NAMES = {
    "FLASK": ["ABYE", "EMPTY", "HALE", "THEWS"],
    "RING": ["ENERGY", "FINAL", "FIRE", "GOLD", "ICE", "JOULE", "RIME", "SUPREME", "VULCAN"],
    "SCROLL": ["SEER", "VISION"],
    "SHIELD": ["BRONZE", "LEATHER", "MITHRIL"],
    "SWORD": ["ELVISH", "IRON", "WOODEN"],
    "TORCH": ["DEAD", "LUNAR", "PINE", "SOLAR"],
}

# Proper names that mark a spent resource: a drunk flask, an exhausted ring,
# a burned-out torch.
_SPENT_NAMES = frozenset({"EMPTY", "GOLD", "DEAD"})

# The classes whose resource can be consumed: torches burn, flasks are drunk,
# rings spend strikes. Swords, shields, and scrolls are merely used and carry
# no consumable flag.
_CONSUMABLE_CLASSES = frozenset({"TORCH", "FLASK", "RING"})

# The pack highlight: bit 7 marks the lit torch, the specifier sits in the
# low bits.
_LIT_BIT = 0x80
_EMPTY_SLOT = 0xFF
_SPECIFIER_MASK = 0x7F

# Built once: specifier index -> (class name, proper name or None). Indices
# 0-5 are the bare classes, unrevealed, and 6-30 the proper names, revealed.
_SPECIFIER_PARTS = [(class_name, None) for class_name in _OBJECT_CLASSES]
for _class_name in _OBJECT_CLASSES:
    for _proper in _OBJECT_PROPER_NAMES[_class_name]:
        _SPECIFIER_PARTS.append((_class_name, _proper))


@dataclass(frozen=True)
class PerceivedObject:
    """One possessed object in the agent's default schema.

    type is the class. specifier is the proper name, or None while
    unrevealed. revealed, consumable, and consuming are the three flags in
    lifecycle order.
    """

    type: str
    specifier: str | None
    revealed: bool
    consumable: bool
    consuming: bool


class PerceivedObjectsWrapper:
    """Translate the perceived observation into the object schema.

    The environment reports hands and pack as specifier indices, the lit
    torch's pack slot carrying a highlight bit, floor objects as their class,
    and the lit torch's minutes in the true state. This wrapper turns those
    into the default object model: each possessed object becomes a
    PerceivedObject and each floor object a class name. It is the modifiable
    default; a developer who wants a different schema edits these constants
    and methods, never the environment.
    """

    def __init__(self, environment) -> None:
        self._environment = environment

    def objects(self, observation: dict) -> dict:
        """Return the current hands, pack, and floor as the object schema."""
        minutes = self._lit_minutes()
        return {
            "hands": [self._possessed(int(byte)) for byte in observation["hands"]],
            "pack": [
                self._possessed(
                    int(byte), active=bool(int(byte) & _LIT_BIT), minutes=minutes
                )
                for byte in observation["pack"]
            ],
            "floor": [self._floor_class(entry) for entry in observation["objects"]],
        }

    def _lit_minutes(self) -> int:
        current_state = self._environment.current_state
        if current_state is None or current_state.lit_torch is None:
            return 0
        return int(current_state.lit_torch[3])

    def _possessed(
        self, byte: int, active: bool = False, minutes: int = 0
    ) -> PerceivedObject | None:
        if byte == _EMPTY_SLOT:
            return None
        class_name, proper = _SPECIFIER_PARTS[byte & _SPECIFIER_MASK]
        if active:
            consuming = minutes > 0
            consumable = minutes > 0
        else:
            consuming = False
            consumable = class_name in _CONSUMABLE_CLASSES and proper not in _SPENT_NAMES
        return PerceivedObject(
            type=class_name,
            specifier=proper,
            revealed=proper is not None,
            consumable=consumable,
            consuming=consuming,
        )

    def _floor_class(self, entry) -> str | None:
        if all(int(byte) == 0 for byte in entry):
            return None
        return _OBJECT_CLASSES[int(entry[0])]