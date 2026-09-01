#!/usr/bin/env bash
# Interactive setup for the Daggorath project.
# Prompts before each step so nothing changes without approval.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROM_DIR="$REPO_DIR/gym/emulation/roms"
HASH_DIR="$REPO_DIR/gym/emulation/hash"
MAME_VERSION="0.289"

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
step() { printf '\n\033[1;36m── Step %s ──\033[0m\n' "$1"; }

yes_no() {
    # Prompt with a default of yes; returns 0 for yes, 1 for no.
    local prompt="$1"
    local answer
    printf '%s [Y/n] ' "$prompt"
    read -r answer
    [[ -z "$answer" || "$answer" =~ ^[Yy]$ ]]
}

build_mame() {
    step "1 of 4: MAME"
    printf '%s\n' \
        "This project needs MAME $MAME_VERSION (the packaged version is too old)." \
        "Building it downloads the source and compiles it (~20 minutes)." \
        "If you already have MAME $MAME_VERSION on this machine, you can skip."
    if ! yes_no "Build MAME $MAME_VERSION from source?"; then
        echo "Skipped MAME build. Using whatever 'mame' is on PATH, if any."
        return
    fi
    echo "Installing build dependencies..."
    sudo apt-get install -y git build-essential python3 libsdl2-dev libsdl2-ttf-dev libfontconfig-dev libpulse-dev qt6-base-dev qt6-base-dev-tools qtchooser
    echo "Cloning MAME source..."
    git clone https://github.com/mamedev/mame.git
    (cd mame && git checkout mame0289)
    echo "Compiling MAME (this is the slow part)..."
    make -C mame -j"$(nproc)"
    echo "Installing MAME..."
    sudo make -C mame install
}

create_venv() {
    step "2 of 4: Python environment"
    echo "Creates .venv in this directory (or reuses it if it already exists)."
    if ! yes_no "Create the Python environment?"; then
        echo "Skipped. Assuming a virtual environment is already active."
        return
    fi
    if [[ -x "$REPO_DIR/.venv/bin/python" ]]; then
        echo ".venv already exists — reusing it."
    else
        python3 -m venv "$REPO_DIR/.venv"
        echo "Created $REPO_DIR/.venv."
    fi
}

install_packages() {
    step "3 of 4: Install packages"
    echo "Installs daggorath-gym and daggorath-agent in editable mode."
    if ! yes_no "Install both packages?"; then
        echo "Skipped package installation."
        return
    fi
    VENV_PY="$REPO_DIR/.venv/bin/python"
    if [[ -x "$VENV_PY" ]]; then
        "$VENV_PY" -m pip install -e "$REPO_DIR/gym" -e "$REPO_DIR/agent"
    else
        echo "No .venv found — run step 2 first." >&2
        exit 1
    fi
}

verify_roms() {
    step "4 of 4: Verify ROMs"
    echo "Checks coco3.zip and daggorath.zip against the expected hashes."
    echo "Verify-only: this step never downloads anything."
    if ! yes_no "Verify the ROMs?"; then
        echo "Skipped. The environment will be unverified."
        return
    fi
    local verify="$REPO_DIR/gym/tools/verify_rom.py"
    if [[ ! -x "$verify" ]]; then
        echo "Verifier not found: $verify" >&2
        exit 1
    fi
    "$REPO_DIR/.venv/bin/python" "$verify" 2>/dev/null \
        || python3 "$verify"
}

say "Daggorath setup"
echo "Each step pauses so you can approve or skip it. Nothing runs without a yes."
build_mame
create_venv
install_packages
verify_roms

say "Setup complete"
echo "Run: .venv/bin/python -m daggorath_agent.train --watch"
