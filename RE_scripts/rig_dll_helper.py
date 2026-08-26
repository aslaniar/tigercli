"""Remote-side half of deploy_client_dll.sh: backup / verify one DLL on Windows.

Usage (run ON THE RIG):
  python rig_dll_helper.py backup  <dll-path>
  python rig_dll_helper.py verify  <dll-path> <expected-sha256-hex> [literal ...]

backup makes <dll>.bak_p2d7_<stamp> next to the file.
verify asserts the file's SHA256 equals the expected hash AND that every
literal byte-string occurs at least once IN the deployed file (lesson 13:
an instrument must be proven present where it will run).
Exits nonzero on any failure; prints machine-checkable lines either way.
"""
import hashlib
import sys
import time


def main(argv):
    if len(argv) < 3:
        print("usage: rig_dll_helper.py backup|verify <dll> [hash] [literals...]")
        return 2
    mode, path = argv[0], argv[1]
    if mode == "backup":
        stamp = time.strftime("%Y%m%d_%H%M%S")
        data = open(path, "rb").read()
        bak = "%s.bak_p2d7_%s" % (path, stamp)
        open(bak, "wb").write(data)
        print("BACKUP %s (%d bytes)" % (bak, len(data)))
        return 0
    if mode == "verify":
        if len(argv) < 4:
            print("VERIFY-FAIL need expected hash")
            return 2
        expect, literals = argv[2].lower(), argv[3:]
        data = open(path, "rb").read()
        got = hashlib.sha256(data).hexdigest()
        if got != expect:
            print("HASH-MISMATCH deployed %s expected %s" % (got, expect))
            return 1
        print("HASH-MATCH %s (%d bytes)" % (got[:16], len(data)))
        ok = True
        for lit in literals:
            n = data.count(lit.encode())
            print("LITERAL %d %s" % (n, lit))
            ok = ok and n >= 1
        return 0 if ok else 1
    print("unknown mode")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
