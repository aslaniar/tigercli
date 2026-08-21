# -*- coding: utf-8 -*-
"""Boot-A settings fix (TRAP 18): restore the byte-exact external settings and flip
external_server.enabled true -> false via a raw byte replace only (the strict parser:
no BOM, no reserialize). The json.dump rewrite (the 113,070-B expansion) was the
'problem reading game content' trip."""
import hashlib
import json
import sys

SRC = r"dcv build\bin\x64\Sunrise\settings.json"
BAK = r"dcv build\bin\x64\Sunrise\settings.json.bak_modepair_ext"

ANCHOR = b'"external_server": {\n      "enabled": true,'


def main():
    data = open(BAK, "rb").read()
    count = data.count(ANCHOR)
    if count != 1:
        print("anchor not unique (%d) - abort" % count)
        sys.exit(1)
    out = data.replace(ANCHOR, b'"external_server": {\n      "enabled": false,', 1)
    assert len(out) == len(data) + 1, "unexpected byte delta"
    assert not out.startswith(b"\xef\xbb\xbf"), "BOM present"
    with open(SRC, "wb") as f:
        f.write(out)
    print("restored + flipped: %d bytes" % len(out))
    print("sha256[:16]: %s" % hashlib.sha256(out).hexdigest()[:16])
    s = json.loads(out.decode("utf-8"))
    mode = "in-process" if not s["client"]["external_server"]["enabled"] else "EXTERNAL (bad)"
    print("mode:", mode)
    print("file_sink:", s["core"]["logging"]["file_sink"],
          "| client level:", s["core"]["logging"]["levels"]["client"])


if __name__ == "__main__":
    main()
