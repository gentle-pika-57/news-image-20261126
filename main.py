#!/usr/bin/env python3
"""Deliver the pre-built poster image for the news-image-20261126 entry.

entry.png is generated ahead of time and shipped with this program. This
program only checks that it is a well-formed 1024x1024 PNG under 1 MiB
and copies it byte-for-byte into the output directory. Standard library
only: no network, no subprocesses, no browser, so it runs on the bare
grading machine exactly as it runs here.
"""

import hashlib
import os
import struct
import sys

ENTRY = "entry.png"
DEFAULT_OUTPUT_DIR = "/output"
OUTPUT_ENV_VAR = "MAKEFUN_OUTPUT_DIR"
WANT_WIDTH = 1024
WANT_HEIGHT = 1024
SIZE_LIMIT = 1_048_576  # 1 MiB

MAGIC = b"\x89PNG\r\n\x1a\n"  # first eight bytes of every PNG file


def die(reason):
    sys.stderr.write("error: %s\n" % reason)
    return 1


def check_png(path):
    """Return None if path is a valid 1024x1024 PNG, else an error string."""
    try:
        st = os.stat(path)
    except OSError as exc:
        return "cannot access %s (%s)" % (path, exc)
    if st.st_size > SIZE_LIMIT:
        return "%s is %d bytes, over the 1 MiB limit" % (path, st.st_size)
    if st.st_size < 24:
        return "%s is %d bytes, too small for a PNG header" % (path, st.st_size)
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
    except OSError as exc:
        return "cannot read %s (%s)" % (path, exc)
    if head[:8] != MAGIC:
        return "%s is missing the PNG signature" % path
    # First chunk after the signature: 4-byte big-endian length, 4-byte
    # type, then data. It must be a 13-byte IHDR whose data opens with
    # the width and height, each a 4-byte big-endian integer.
    chunk_len = struct.unpack(">I", head[8:12])[0]
    if head[12:16] != b"IHDR" or chunk_len != 13:
        return "%s has no valid IHDR chunk" % path
    width, height = struct.unpack(">II", head[16:24])
    if (width, height) != (WANT_WIDTH, WANT_HEIGHT):
        return "%s is %dx%d, expected %dx%d" % (path, width, height, WANT_WIDTH, WANT_HEIGHT)
    return None


def digest(path):
    """SHA-256 of a file, read in chunks."""
    hasher = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(65536)
            if not block:
                break
            hasher.update(block)
    return hasher.hexdigest()


def run():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, ENTRY)

    problem = check_png(source)
    if problem:
        return die(problem)

    out_dir = os.environ.get(OUTPUT_ENV_VAR) or DEFAULT_OUTPUT_DIR
    target = os.path.join(out_dir, ENTRY)

    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(source, "rb") as src, open(target, "wb") as dst:
            while True:
                block = src.read(65536)
                if not block:
                    break
                dst.write(block)
    except OSError as exc:
        return die("cannot copy %s to %s (%s)" % (source, target, exc))

    try:
        if os.path.getsize(target) != os.path.getsize(source):
            return die("copied file size mismatch: %s" % target)
        if digest(target) != digest(source):
            return die("copied file digest mismatch: %s" % target)
    except OSError as exc:
        return die("cannot verify %s (%s)" % (target, exc))

    print("wrote %s (%d bytes)" % (target, os.path.getsize(source)))
    return 0


if __name__ == "__main__":
    sys.exit(run())
