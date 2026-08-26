#!/usr/bin/env python3
"""Re-band the rig's LOCAL legacy identity block onto the slot-1 soid band.

The rig client walks the single-account init path, so its own identity comes
from `state.account` / `state.characters` - NOT from `state.accounts[]`, which
the client never walks (FINDINGS 20.14). Those four values must therefore name
the band the server provisioned for slot 1, or ws-503 adopts the legacy soid
into slot 1 and rebases it onto slot 0's keys (FINDINGS 20.17).

The four target strings each appear TWICE in the file - once in the legacy
block and once in `state.accounts[0]`, which must NOT move. This does offset
surgery bounded to the region outside the `accounts` array, verifies the result
by re-parsing, and writes only when every assertion holds.

Usage: resoid_settings.py <in.json> <out.json>
"""
import json
import sys

FROM_BAND = "0x9EAA30010010"
TO_BAND = "0x9EAA30010011"
SUFFIXES = ("0100", "0101", "0102", "0103")

# The server's provisioned slot-1 primary, read from the Mac's settings.json
# (state.accounts[1].account.primary_soid). The band constants above are checked
# against THIS, never against themselves: a first draft flipped the wrong digit
# and produced a plausible-looking 0x9EAA30011010_0100 that matched no slot.
EXPECTED_PRIMARY = "0x9EAA300100110100"


def array_span(text, key):
    """@return (start, end) covering the array value of `key`, brackets included."""
    marker = '"%s"' % key
    if text.count(marker) != 1:
        raise SystemExit("expected exactly one %s key, found %d"
                         % (marker, text.count(marker)))
    cursor = text.index(marker) + len(marker)
    while text[cursor] in " \t\r\n:":
        cursor += 1
    if text[cursor] != "[":
        raise SystemExit("%s is not an array (found %r)" % (key, text[cursor]))
    start = cursor
    depth = 0
    in_string = False
    escaped = False
    while cursor < len(text):
        char = text[cursor]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
            if depth == 0:
                return start, cursor + 1
        cursor += 1
    raise SystemExit("unterminated %s array" % key)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    source, destination = sys.argv[1], sys.argv[2]
    with open(source, "r", encoding="utf-8") as handle:
        text = handle.read()

    original = json.loads(text)
    accounts_start, accounts_end = array_span(text, "accounts")
    print("accounts array span: [%d, %d)" % (accounts_start, accounts_end))

    edits = 0
    for suffix in SUFFIXES:
        old = '"%s%s"' % (FROM_BAND, suffix)
        new = '"%s%s"' % (TO_BAND, suffix)
        if len(old) != len(new):
            raise SystemExit("replacement changes length for %s" % suffix)
        positions = []
        at = text.find(old)
        while at != -1:
            positions.append(at)
            at = text.find(old, at + 1)
        outside = [p for p in positions if not (accounts_start <= p < accounts_end)]
        print("  %s -> %s  occurrences=%d outside_accounts=%d"
              % (old, new, len(positions), len(outside)))
        if len(positions) != 2 or len(outside) != 1:
            raise SystemExit("unexpected occurrence layout for %s" % suffix)
        at = outside[0]
        text = text[:at] + new + text[at + len(old):]
        edits += 1
    if edits != 4:
        raise SystemExit("expected 4 edits, made %d" % edits)

    # VERIFY BEFORE WRITING. The result must parse, the legacy block must name
    # the new band, and every provisioned slot must be byte-for-byte untouched.
    updated = json.loads(text)
    expected_primary = TO_BAND + "0100"
    if expected_primary != EXPECTED_PRIMARY:
        raise SystemExit("band constants produce %s, but slot 1 is %s"
                         % (expected_primary, EXPECTED_PRIMARY))
    if updated["state"]["account"]["primary_soid"] != expected_primary:
        raise SystemExit("legacy primary_soid did not move")
    characters = updated["state"]["characters"]
    if len(characters) != 3:
        raise SystemExit("unexpected legacy character count %d" % len(characters))
    for index, character in enumerate(characters):
        want = TO_BAND + SUFFIXES[index + 1]
        if character["soid"] != want:
            raise SystemExit("legacy character %d is %s, wanted %s"
                             % (index, character["soid"], want))
    if updated["state"]["accounts"] != original["state"]["accounts"]:
        raise SystemExit("state.accounts changed - refusing to write")
    original["state"]["account"] = updated["state"]["account"]
    original["state"]["characters"] = updated["state"]["characters"]
    if updated != original:
        raise SystemExit("a field outside the legacy identity block changed")

    with open(source, "r", encoding="utf-8") as handle:
        before = handle.read()
    if len(before) != len(text):
        raise SystemExit("length changed: %d -> %d" % (len(before), len(text)))
    differing = [i for i in range(len(before)) if before[i] != text[i]]
    print("differing characters: %d at %s" % (len(differing), differing))
    if len(differing) != 4:
        raise SystemExit("expected exactly 4 differing characters")

    with open(destination, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("wrote %s (%d bytes)" % (destination, len(text)))
    print("state.account.primary_soid = %s" % updated["state"]["account"]["primary_soid"])
    print("state.characters[].soid    = %s"
          % ", ".join(c["soid"] for c in updated["state"]["characters"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
