"""Restore and verify the byte-identical reproducibility ZIP, without networking."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile


EXPECTED_ARCHIVE = "Supplementary_Reproducibility_Anonymous.zip"
EXPECTED_SIZE = 76_957_617
EXPECTED_SHA256 = "786758bf2b361e821f0a58bfca65a8669dccc3dfde5cede689b6e5594643fbff"
BUFFER_SIZE = 1024 * 1024


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(BUFFER_SIZE)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(folder):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if (
        manifest.get("archive_name") != EXPECTED_ARCHIVE
        or manifest.get("archive_size") != EXPECTED_SIZE
        or manifest.get("archive_sha256") != EXPECTED_SHA256
        or manifest.get("part_size_limit") != 7 * 1024 * 1024
    ):
        raise ValueError("Manifest does not identify the expected original archive.")
    parts = manifest.get("parts", [])
    if len(parts) != 11:
        raise ValueError("Exactly eleven archive parts are required.")
    if sum(part.get("size", 0) for part in parts) != EXPECTED_SIZE:
        raise ValueError("Manifest part sizes do not sum to the archive size.")
    for index, part in enumerate(parts, start=1):
        expected_name = "reproducibility.part{:02d}.bin".format(index)
        if part.get("name") != expected_name:
            raise ValueError("Unexpected part name or order in manifest.")
        if not 0 < part.get("size", 0) <= 7 * 1024 * 1024:
            raise ValueError("Invalid part size in manifest.")
        path = folder / expected_name
        if not path.is_file():
            raise FileNotFoundError("Missing archive part: " + expected_name)
        if path.stat().st_size != part["size"]:
            raise ValueError("Incorrect file size: " + expected_name)
        if file_digest(path) != part.get("sha256"):
            raise ValueError("SHA-256 mismatch: " + expected_name)
        print("Verified " + expected_name)
    return parts


def check_archive(path):
    if path.stat().st_size != EXPECTED_SIZE or file_digest(path) != EXPECTED_SHA256:
        raise ValueError("Restored ZIP differs from the original archive.")
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            raise ValueError("ZIP member CRC failed: " + bad_member)
        members = sum(not item.is_dir() for item in archive.infolist())
    print("Verified original ZIP: {:,} bytes; {} files; all member CRCs pass.".format(
        EXPECTED_SIZE, members))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Existing directory in which to restore the ZIP (default: script directory).")
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    output_dir = folder if args.output_dir is None else args.output_dir.resolve()
    if not output_dir.is_dir():
        raise ValueError("The output directory must already exist.")
    parts = validate_manifest(folder)
    destination = output_dir / EXPECTED_ARCHIVE
    if destination.exists():
        check_archive(destination)
        print("An identical archive already exists; it was left unchanged.")
        return
    temporary = output_dir / (EXPECTED_ARCHIVE + ".partial")
    try:
        with temporary.open("xb") as stream:
            digest = hashlib.sha256()
            for part in parts:
                with (folder / part["name"]).open("rb") as source:
                    while True:
                        block = source.read(BUFFER_SIZE)
                        if not block:
                            break
                        stream.write(block)
                        digest.update(block)
            if digest.hexdigest() != EXPECTED_SHA256:
                raise ValueError("Restored ZIP SHA-256 verification failed.")
        check_archive(temporary)
        # The final archive must not already exist; do not overwrite user files.
        if destination.exists():
            raise FileExistsError("The output archive appeared during restoration.")
        os.rename(temporary, destination)
    except Exception:
        # A pre-existing partial file was not created by this run and must remain.
        if "stream" in locals() and temporary.exists():
            temporary.unlink()
        raise
    print("Restored: " + destination.name)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print("Restoration stopped: " + str(error), file=sys.stderr)
        sys.exit(1)
