"""Offline stdlib-only entrypoint for the rendered news image.

The image is rendered offline at build time by art/render.py using Pillow;
Pillow is never imported here.  This program is the stdlib-only copier that
the grader runs: it validates the committed asset and writes its exact bytes.
"""

import os
import struct
import sys


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1048576
IMAGE_SIZE = 1024


class GateFailure(Exception):
    """A specific competition rule failure."""


def validate_asset(data):
    """Validate every required property of the committed PNG."""
    if data[:8] != PNG_SIGNATURE:
        raise GateFailure("rule failed: the file does not have a PNG signature")
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise GateFailure("rule failed: bytes 12-15 are not the IHDR marker")
    if len(data) > MAX_BYTES:
        raise GateFailure("rule failed: image is larger than 1048576 bytes")
    width, height = struct.unpack(">II", data[16:24])
    if width != IMAGE_SIZE or height != IMAGE_SIZE:
        raise GateFailure(f"rule failed: PNG dimensions are {width}x{height}, not 1024x1024")
    if len(data) < 12 or data[-12:-8] != b"\x00\x00\x00\x00" or data[-8:-4] != b"IEND":
        raise GateFailure("rule failed: PNG does not end with a valid IEND chunk")


def main():
    arguments = list(sys.argv[1:])
    verify_only = "--verify-only" in arguments
    if verify_only:
        arguments.remove("--verify-only")
    repo_root = os.path.abspath(arguments[0] if arguments else os.path.dirname(__file__))
    source_path = os.path.join(repo_root, "art", "entry.png")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    output_path = os.path.join(outdir, "entry.png")

    with open(source_path, "rb") as source_file:
        data = source_file.read()
    validate_asset(data)

    if verify_only:
        if os.path.exists(output_path):
            with open(output_path, "rb") as output_file:
                existing = output_file.read()
            assert existing == data, "existing output differs from source"
        print(f"{source_path} {len(data)} entry.png 1024x1024")
        return

    os.makedirs(outdir, exist_ok=True)
    with open(output_path, "wb") as output_file:
        output_file.write(data)

    written = os.path.getsize(output_path)
    if written != len(data):
        raise GateFailure(
            f"rule failed: wrote {written} bytes but read {len(data)} bytes"
        )
    print(f"{source_path} {len(data)} entry.png 1024x1024")


if __name__ == "__main__":
    try:
        main()
    except (GateFailure, OSError, struct.error) as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        raise SystemExit(1)
