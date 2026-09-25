"""Unit tests for PerceivedObjectsWrapper — no MAME needed."""

from daggorath_agent.wrappers import PerceivedObjectsWrapper
from daggorath_gym.state import (
    FLOOR_OBJECTS_BYTES,
    FRAME_LEN,
    HANDS_BYTES,
    OBJECT_RAW_BYTES,
    OBJECTS_BYTES,
    PACK_BYTES,
    TORCH_RAW_BYTES,
    DaggorathState,
)

# The EXAMINE display sentinel from state.py; the pack is only perceived in
# that mode.
_EXAMINE = 0xD495


def _frame():
    frame = bytearray(FRAME_LEN)
    frame[1] = _EXAMINE & 0xFF  # display_function, low byte
    frame[2] = (_EXAMINE >> 8) & 0xFF  # high byte
    return bytes(frame)


def _objects(pack=(), torch=(0xFF, 0xFF, 0xFF, 0, 0, 0)):
    payload = bytearray([0xFF] * OBJECTS_BYTES)
    for index, (class_byte, proper, reveal) in enumerate(pack):
        offset = HANDS_BYTES + index * OBJECT_RAW_BYTES
        payload[offset] = class_byte
        payload[offset + 1] = proper
        payload[offset + 2] = reveal
    torch_offset = HANDS_BYTES + PACK_BYTES + FLOOR_OBJECTS_BYTES
    payload[torch_offset:torch_offset + TORCH_RAW_BYTES] = torch
    return bytes(payload)


class _FakeEnvironment:
    def __init__(self, state):
        self.current_state = state


def test_possessed_objects():
    """The wrapper turns pack specifiers and the lit bit into the schema."""
    state = DaggorathState(
        _frame(),
        objects=_objects(
            pack=(
                (5, 0x0F, 0),  # PINE TORCH, the lit one
                (4, 0x11, 0),  # WOODEN SWORD
                (5, 0x18, 0),  # DEAD TORCH
            ),
            torch=(5, 0x0F, 0, 15, 7, 0),  # the lit PINE TORCH, 15 minutes
        ),
    )
    wrapper = PerceivedObjectsWrapper(_FakeEnvironment(state))
    objects = wrapper.objects(state.as_perceived())

    torch, sword, dead = objects["pack"][:3]
    assert torch.type == "TORCH"
    assert torch.specifier == "PINE"
    assert torch.revealed is True
    assert torch.consumable is True
    assert torch.consuming is True

    assert sword.type == "SWORD"
    assert sword.specifier == "WOODEN"
    assert sword.revealed is True
    assert sword.consumable is True
    assert sword.consuming is False

    assert dead.type == "TORCH"
    assert dead.specifier == "DEAD"
    assert dead.consumable is False
    assert dead.consuming is False

    assert objects["pack"][3] is None  # an empty slot reads as nothing


def test_lit_torch_with_no_minutes_is_not_consuming():
    """A torch still marked lit but at zero minutes is not burning."""
    state = DaggorathState(
        _frame(),
        objects=_objects(
            pack=((5, 0x0F, 0),),
            torch=(5, 0x0F, 0, 0, 0, 0),  # the lit PINE TORCH, burned out
        ),
    )
    wrapper = PerceivedObjectsWrapper(_FakeEnvironment(state))
    torch = wrapper.objects(state.as_perceived())["pack"][0]

    assert torch.consuming is False
    assert torch.consumable is False
