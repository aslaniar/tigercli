#!/usr/bin/env python3
"""Phase 0 audit helpers (read-only). Run from the workspace root."""
import json, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORK = os.path.join(ROOT, "RE_build", "Sunrise-fork")

def find_tokens(d, out):
    if isinstance(d, dict):
        for k, v in d.items():
            kl = k.lower()
            if any(t in kl for t in ("token", "secret", "authenticationkey", "encryptionkey")):
                if isinstance(v, str) and v:
                    out.append((k, v))
            find_tokens(v, out)
    elif isinstance(d, list):
        for v in d:
            find_tokens(v, out)

def main():
    # 1. collect token-shaped values from both runtime settings files
    values = []
    for path in (os.path.join(ROOT, "RE_output", "s1_accept", "settings.json"),
                 os.path.join(ROOT, "Game", "bin", "x64", "Sunrise", "settings.json")):
        try:
            with open(path) as f:
                find_tokens(json.load(f), values)
        except Exception as e:
            print(f"!! {path}: {e}")
    print("== token-shaped runtime values ==")
    for k, v in values:
        print(f"  {k}: len={len(v)} prefix={v[:12]!r}")
    # 2. sweep all refs for those values
    refs = subprocess.run(["git", "-C", FORK, "for-each-ref", "--format=%(refname)"],
                          capture_output=True, text=True).stdout.split()
    print("== refs swept ==", refs)
    for k, v in values:
        if len(v) < 8:
            continue
        hits = []
        for ref in refs:
            r = subprocess.run(["git", "-C", FORK, "grep", "-l", v, ref],
                               capture_output=True, text=True)
            if r.returncode == 0:
                hits.append(ref)
        print(f"  value {k}: {'CLEAN' if not hits else 'HIT in ' + str(hits)}")
    # 3. committed settings.json paths across all history
    names = subprocess.run(["git", "-C", FORK, "log", "--all", "--format=", "--name-only"],
                           capture_output=True, text=True).stdout
    settings = sorted(set(n for n in names.splitlines() if "settings.json" in n))
    print("== settings.json ever committed ==")
    for n in settings:
        print("  ", n)
    # 4. default_settings.json: secret-shaped fields?
    try:
        with open(os.path.join(FORK, "Sunrise", "resources", "default_settings.json")) as f:
            d = json.load(f)
        found = []
        find_tokens(d, found)
        print("== default_settings.json token-shaped ==", found if found else "none")
    except Exception as e:
        print("!! default_settings:", e)

if __name__ == "__main__":
    main()