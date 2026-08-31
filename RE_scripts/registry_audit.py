#!/usr/bin/env python3
"""registry_audit.py - verify TOOLS.md registry rows against tool reality.

Two checks per row:
  1. EXISTENCE: the named RE_scripts path exists.
  2. CAPS EXACT-MATCH: the row's [caps: ...] tag must equal the tool's
     declared `# REGISTRY: caps:` line (set comparison). Drift = named diff:
     row-only caps are OVERCLAIMS (capability the tool lacks - the 08-31
     rig_dll_helper class), tool-only caps are UNDECLARED (capability the
     registry does not advertise).
Rows without a caps tag warn UNDECLARED - annotate them; they are not yet
deterministically verified. Rows without an RE_scripts path (command
recipes) are skipped.

Usage: /usr/bin/python3 RE_scripts/registry_audit.py
Exit: 0 all verified/declared; 1 drift found; 2 usage.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "TOOLS.md")


def rows_from_tools_md():
    out = []
    for line in open(TOOLS, encoding="utf8"):
        m = re.match(r"\|\s*(RE_scripts/[^|\s]+)\s*\|", line)
        if m:
            caps_m = re.search(r"\[caps:\s*([^\]]+)\]", line)
            caps = {c.strip() for c in caps_m.group(1).split(",")} \
                if caps_m else set()
            out.append((m.group(1), caps, line.strip()))
    return out


def tool_caps(path):
    """Extract the declared caps from the tool's # REGISTRY: line."""
    try:
        src = open(path, encoding="utf8", errors="replace").read(4000)
    except OSError:
        return None
    m = re.search(r"^#\s*REGISTRY:\s*caps:\s*(.+)$", src, re.M)
    if not m:
        return None
    return {c.strip() for c in m.group(1).split(",")}


def main():
    if not os.path.exists(TOOLS):
        print("ERROR: no TOOLS.md at %s" % TOOLS)
        return 2
    rows = rows_from_tools_md()
    print("registry rows naming RE_scripts tools: %d" % len(rows))
    fails = []
    warns = []
    verified = 0
    for path, row_caps, line in rows:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            fails.append("MISSING FILE: %s" % path)
            continue
        declared = tool_caps(full)
        if declared is None:
            warns.append("UNDECLARED: %s (no # REGISTRY: caps: line)"
                         % path)
            continue
        if not row_caps:
            warns.append("ROW WITHOUT CAPS TAG: %s" % path)
            continue
        over = row_caps - declared
        under = declared - row_caps
        if over or under:
            fails.append("CAPS DRIFT: %s | row-overclaim=%s | "
                         "tool-undeclared=%s" %
                         (path, sorted(over) or "-", sorted(under) or "-"))
        else:
            verified += 1
    print("caps-verified: %d | undeclared: %d | drift: %d" %
          (verified, len(warns), len(fails)))
    for w in warns:
        print("  WARN %s" % w)
    if fails:
        print("REGISTRY DRIFT (%d) - fix the row or the tool:" % len(fails))
        for f in fails:
            print("  - %s" % f)
        return 1
    print("REGISTRY AUDIT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
