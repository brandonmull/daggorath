#!/usr/bin/env python3
"""Verify the ROMs the Daggorath environment needs.

The Daggorath cartridge ROM is checked against the hashes in coco_cart.xml.
The CoCo 3 system ROMs (coco3.rom, disk11.rom) have no hash source in this
repo, so they are verified by presence inside coco3.zip.

Verify-only: this script never downloads anything.
"""
import hashlib
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
import zlib

REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROM_DIR = os.path.join(REPO_DIR, "gym", "emulation", "roms")
HASH_FILE = os.path.join(REPO_DIR, "gym", "emulation", "hash", "coco_cart.xml")

DAGGORATH_ROM = "Dungeons of Daggorath (shield fix).rom"
COCO3_ROMS = ("coco3.rom", "disk11.rom")


def _expected_hashes():
    """Map rom filename -> (size, crc, sha1) from coco_cart.xml."""
    expected = {}
    for rom in ET.parse(HASH_FILE).iter("rom"):
        name = rom.get("name")
        if name and rom.get("size") and rom.get("crc") and rom.get("sha1"):
            expected[name] = (
                int(rom.get("size")),
                rom.get("crc").lower(),
                rom.get("sha1").lower(),
            )
    return expected


def _sha1(data):
    return hashlib.sha1(data).hexdigest()


def _crc32(data):
    return "%08x" % (zlib.crc32(data) & 0xFFFFFFFF)


def verify_daggorath():
    zpath = os.path.join(ROM_DIR, "daggorath.zip")
    if not os.path.exists(zpath):
        print(f"MISSING: {zpath}")
        print("Supply the Daggorath ROM; it is not downloaded here.")
        return False

    expected = _expected_hashes().get(DAGGORATH_ROM)
    if expected is None:
        print(f"No expected hash for {DAGGORATH_ROM} in coco_cart.xml.")
        return False

    with zipfile.ZipFile(zpath) as zf:
        if DAGGORATH_ROM not in zf.namelist():
            print(f"MISSING inside daggorath.zip: {DAGGORATH_ROM}")
            return False
        data = zf.read(DAGGORATH_ROM)

    exp_size, exp_crc, exp_sha1 = expected
    if len(data) == exp_size and _crc32(data) == exp_crc and _sha1(data) == exp_sha1:
        print(f"OK: {DAGGORATH_ROM} (crc {exp_crc})")
        return True

    print(f"MISMATCH: {DAGGORATH_ROM}")
    print(f"  expected crc  {exp_crc}  sha1 {exp_sha1}")
    print(f"  actual   crc  {_crc32(data)}  sha1 {_sha1(data)}")
    return False


def verify_coco3():
    zpath = os.path.join(ROM_DIR, "coco3.zip")
    if not os.path.exists(zpath):
        print(f"MISSING: {zpath}")
        print("Supply the CoCo 3 system ROMs; they are not downloaded here.")
        return False

    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        for rom in COCO3_ROMS:
            if rom not in names:
                print(f"MISSING inside coco3.zip: {rom}")
                return False

    print(f"OK: coco3.zip contains {', '.join(COCO3_ROMS)}")
    return True


def main():
    ok = True
    ok &= verify_daggorath()
    ok &= verify_coco3()
    if not ok:
        print("\nVerification FAILED — the environment will not run without the ROMs.")
        sys.exit(1)
    print("\nVerification PASSED.")


if __name__ == "__main__":
    main()
