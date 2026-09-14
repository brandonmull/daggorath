"""The paths and machine both machine-save-load experiments share."""

from pathlib import Path

SANDBOX_PATH = Path(__file__).resolve().parent
GYM_PATH = SANDBOX_PATH.parent.parent

# The CoCo 3 cannot save states at all — MAME marks every CoCo 3 driver
# savestate="unsupported" — so both experiments run on the CoCo 2B, whose
# states are supported. A state written on one machine cannot be loaded on
# the other.
MACHINE_NAME = "coco2b"

STATE_DIRECTORY = GYM_PATH / ".mame" / "state"

# -pluginspath replaces MAME's search path, so MAME's own plugins directory has
# to be named alongside the sandbox's or boot.lua cannot be found.
MAME_PLUGIN_PATH = "/usr/local/share/games/mame/plugins"
