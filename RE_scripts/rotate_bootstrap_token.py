#!/usr/bin/env python3
"""Phase 1: rotate bootstrap_token to a fresh random value + placeholder defaults.
- runtime settings (both trees' deployed configs get the REAL new value)
- compiled default + default_settings.json (both trees get a zero placeholder)
The OLD constant (2MFioXto7iAUN4Qj) is burned; history stays untouched.
"""
import json, os, secrets

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORK = os.path.join(ROOT, "RE_build", "Sunrise-fork", "Sunrise")
INV = os.path.join(ROOT, "RE_build", "Sunrise-fork-inventory", "Sunrise")

NEW = secrets.token_hex(16)
PLACEHOLDER = "0" * 32
print("new runtime token:", NEW)

targets = {
    "RE_output/s1_accept/settings.json": None,          # server runtime (add key)
    "Game/bin/x64/Sunrise/settings.json": None,         # client runtime (update key)
}
for path, _ in targets.items():
    p = os.path.join(ROOT, path)
    d = json.load(open(p))
    if "server" in d and isinstance(d["server"], dict):
        d["server"]["bootstrap_token"] = NEW
    else:
        raise SystemExit(f"!! no server block in {path}")
    json.dump(d, open(p, "w"), indent=2)
    print(f"runtime updated: {path}")

# compiled defaults + default_settings.json in BOTH trees
for tree_name, tree in (("fork", FORK), ("inventory", INV)):
    dh = os.path.join(tree, "src", "core", "settings", "server", "definition.h")
    s = open(dh, "r", encoding="utf-8").read()
    import re
    s2 = re.sub(r'bootstrapToken\{"[0-9A-Fa-f]{32}"\}',
                f'bootstrapToken{{"{PLACEHOLDER}"}}', s)
    if s2 == s:
        raise SystemExit(f"!! no token literal found in {dh}")
    open(dh, "w", encoding="utf-8").write(s2)
    print(f"definition.h placeholder: {tree_name}")
    ds = os.path.join(tree, "resources", "default_settings.json")
    j = json.load(open(ds))
    j["server"]["bootstrap_token"] = PLACEHOLDER
    json.dump(j, open(ds, "w"), indent=2)
    print(f"default_settings.json placeholder: {tree_name}")