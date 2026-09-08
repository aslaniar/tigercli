#!/usr/bin/env python3
# REGISTRY: caps: identity-dumpcheck, p2-204-readout
"""Boot-end identity dump check (p2-204): is the type-51 echo even right?

Compares the echo the fork SENT (the `echo=` hex on the server's
`stage=bubble_startup push` line - the bytes actually sent, derived-lines
rule) against the RECEIVING client's own identity row held in a boot-end
dump: DAT_1426BDCC8 row 2 (RVA 0x26BDCC8, stride 0x70), window
[row+0x02 .. row+0x57] = the 0x56-byte SteamNetworkingIdentity form the
client's validator memcmps (20.328 R3 + type54-and-receiver-gate.md CLAIM 6g:
header 01 01 @+0, ascii "steamid:<id>#<token>" @+0x02, zero pad @+0x2C,
version byte 0x06 @+0x55).

The runtime address of the table differs per dump: the script reads the
destiny2 module base OUT of the dump (minidump_reader summary) and adds the
RVA - never assume 0x7FF6... (the 20.326 R1 class).

Usage:
  python3 RE_scripts/identity_dumpcheck.py --log <server.log> \
      --dump <full minidump> [--who MAC|RIG]
Exit 0 = every dump-checkable push matched its client's row. Exit 1 = a
mismatch, an unreadable row, or no push logged. Exit 2 = usage error.
"""

import argparse
import re
import sys

from minidump_reader import Minidump

TABLE_RVA = 0x26BDCC8  # DAT_1426BDCC8 - 0x140000000
ROW2_OFFSET = 0x70     # stride 0x70, row k = base + (k-1)*0x70
WINDOW_OFFSET = 0x02   # identity window start inside the row
WINDOW_LEN = 0x56      # 42 ascii + 43 pad + version byte


def find_destiny_module(md):
    for m in md.modules:
        name = (m.get("name") or "").lower()
        if "destiny2" in name and name.endswith(".exe"):
            return m
    return None


def read_identity_window(md, module):
    runtime = module["base"] + TABLE_RVA + ROW2_OFFSET + WINDOW_OFFSET
    data = md.read_va(runtime, WINDOW_LEN)
    return runtime, data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True, help="server sunrise.log (the p2-204 archive)")
    ap.add_argument("--dump", required=True, help="full minidump of the client")
    ap.add_argument("--who", default=None, help="expected echo owner label, optional")
    args = ap.parse_args()

    pushes = []
    with open(args.log, "rb") as f:
        for line in f:
            s = line.decode(errors="replace")
            m = re.search(
                r"stage=bubble_startup push session=0x([0-9A-Fa-f]+) "
                r"lookup_key=(?:0x)?([0-9A-Fa-f]+) member_key=0x[0-9A-Fa-f]+ "
                r"result=stored bytes=\d+ echo=([0-9A-Fa-f]+)",
                s)
            if m:
                pushes.append((m.group(1), m.group(2), m.group(3)))
    if not pushes:
        print("DUMPCHECK: no stage=bubble_startup push/echo lines in the log")
        return 1

    md = Minidump(args.dump)
    module = find_destiny_module(md)
    if module is None:
        print("DUMPCHECK: destiny2 module not found in dump")
        return 1
    runtime, window = read_identity_window(md, module)
    if len(window) != WINDOW_LEN:
        print(f"DUMPCHECK: identity window unreadable at 0x{runtime:X} "
              f"(got {len(window)} of {WINDOW_LEN} bytes)")
        return 1

    client_ascii = window[:42].decode("ascii", errors="replace")
    client_version = window[0x55]
    print(f"DUMPCHECK: client row 0x{runtime - WINDOW_OFFSET:X} "
          f"identity='{client_ascii}' version=0x{client_version:02X}")
    client_hex = window.hex().upper()

    failed = False
    for session, key, echo in pushes:
        match = echo == client_hex
        print(f"DUMPCHECK: push session=0x{session} lookup_key=0x{key} "
              f"echo={'MATCHES client row' if match else 'DIFFERS from client row'}")
        if match:
            continue
        failed = True
        first = next((i for i, (a, b) in enumerate(zip(echo, client_hex)) if a != b), None)
        print(f"DUMPCHECK:   first hex-nibble difference at offset {first} "
              f"(echo {echo[max(0, first - 8):first + 16]} vs "
              f"client {client_hex[max(0, first - 8):first + 16]})")
        if args.who:
            print(f"DUMPCHECK:   expected owner per caller: {args.who}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())