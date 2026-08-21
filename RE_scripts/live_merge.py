#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""live_merge.py - the RAW live merge of the Sunrise server + client logs.

Tails both logs in one window; every new line is printed verbatim (the log's
own bytes always pass through untouched) with a minimal [SERVER] / [CLIENT]
prefix, interleaved by arrival order (both files are polled each tick; no
clock math). Rotation-safe: the file sizes are polled, and a shrink (the game
truncates/rotates its log at each launch) re-seeks to 0. Partial trailing
lines are held back until their newline arrives.

Presentation: ONLY the [SERVER] / [CLIENT] prefixes carry color ([SERVER] =
bright purple, [CLIENT] = green); the log line's content stays white.

Usage:  python -X utf8 RE_scripts/live_merge.py [--server LOG] [--client LOG]
Quit:   Ctrl+C
"""
import argparse
import os
import sys
import time

POLL = 0.1  # seconds between size polls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_LOG = os.path.join(ROOT, "RE_output", "s1_accept", "Sunrise", "logs", "sunrise.log")
CLIENT_LOG = os.path.join(ROOT, "dcv build", "bin", "x64", "Sunrise", "logs", "sunrise.log")

# --- the presentation colors ------------------------------------------------
# ONLY the prefixes carry color; the log line's content stays white (the
# default). The codes wrap nothing else.
C_SERVER = b"\x1b[95m"      # the bright purple [SERVER] prefix (readable)
C_CLIENT = b"\x1b[32m"      # the green [CLIENT] prefix
RESET = b"\x1b[0m"


def _size(path):
    """The file's current size; -1 when the file is missing/unreadable."""
    try:
        return os.path.getsize(path)
    except OSError:
        return -1


class Tail:
    """One seek-based log follower (bytes-verbatim, rotation-safe)."""

    def __init__(self, path, prefix, prefix_color):
        self.path = path
        self.prefix = prefix.encode("utf-8")    # b"[SERVER] " / b"[CLIENT] "
        self.prefix_color = prefix_color        # the ANSI bytes for the prefix
        self.pos = max(_size(path), 0)          # start at the end: tail from now on
        self.partial = b""                      # the held-back incomplete line

    def poll(self, emit):
        """Read the new bytes; emit() each complete line, hold back the tail."""
        size = _size(self.path)
        if size < 0:
            return
        if size < self.pos:
            # the log was truncated/rotated (the game's launch): re-seek to 0
            self.pos = 0
            self.partial = b""
        if size == self.pos:
            return
        try:
            with open(self.path, "rb") as f:
                old = self.pos
                f.seek(old)
                data = f.read()
                self.pos = f.seek(0, 2)         # the real EOF (self-heals a mid-read shrink)
                if self.pos < old:              # shrunk mid-read: drop the old partial
                    self.partial = b""
        except OSError:
            return
        if not data:
            return
        chunks = (self.partial + data).split(b"\n")
        self.partial = chunks.pop()             # no newline yet -> hold it back
        for line in chunks:
            # the colored prefix, then the white content, then the reset.
            emit(self.prefix_color + self.prefix + RESET + line + b"\n")


def main():
    ap = argparse.ArgumentParser(description="RAW live merge of the Sunrise server + client logs")
    ap.add_argument("--server", default=SERVER_LOG, help="the server log path")
    ap.add_argument("--client", default=CLIENT_LOG, help="the client log path")
    args = ap.parse_args()

    if os.name == "nt":
        os.system("")   # the Windows VT enable (the ANSI colors)

    raw = getattr(sys.stdout, "buffer", None)

    def emit(data):
        """Write one record (bytes) and flush; degrade gracefully on odd bytes."""
        if raw is not None:
            try:
                raw.write(data)
                raw.flush()
                return
            except UnicodeError:
                pass                            # a console raw layer needs valid UTF-8
        try:
            sys.stdout.write(data.decode("utf-8", "replace"))
        except UnicodeError:
            pass                                # drop the line rather than crash
        sys.stdout.flush()

    emit(("[LIVE MERGE] server=%s client=%s | the client log rotates at the game's "
          "launch: after a rotation the [CLIENT] lines go quiet until this script "
          "is restarted\n" % (args.server, args.client)).encode("utf-8"))

    tails = [Tail(args.server, "[SERVER] ", C_SERVER),
             Tail(args.client, "[CLIENT] ", C_CLIENT)]
    try:
        while True:
            for tail in tails:
                tail.poll(emit)
            time.sleep(POLL)
    except KeyboardInterrupt:
        pass
    emit(b"live_merge stopped.\n")


if __name__ == "__main__":
    main()
