# ROMs Stay in the Repo

The ROMs stay in the repo for now (`gym/emulation/roms/`), and the docs say so —
they ship with the repo, so no placement is needed.

The setup script and `verify_rom.py` are verify-only: they check hashes and never
download.

If the files are ever removed from the repo and history, the README wording flips
to "you supply them," and the verify step becomes the gate it already is.
