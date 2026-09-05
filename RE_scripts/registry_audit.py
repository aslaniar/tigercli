#!/usr/bin/env python3
# REGISTRY: caps: registry-audit, tree-direction, router-check
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

Tree-direction checks (backlog 1.8 / red-team H4+M5 - the original audit only
ran TOOLS.md -> disk, so the reverse drift class was invisible):
  3. REVERSE ROW CHECK: a tool under RE_scripts/ that declares
     `# REGISTRY: caps:` but has NO TOOLS.md row = drift (the tool exists
     but the registry cannot vouch for it).
  4. ROUTER FILE CHECK: every PATHED file reference in AGENTS.md (the
     router) must exist on disk (MISSING = fail, the dump_search class);
     pathed files that exist but are untracked in git warn (drift until
     committed). Bare-name mentions and RE_output/RE_build references are
     prose/generated - skipped by design (RE_output trees are gitignored).

Usage: /usr/bin/python3 RE_scripts/registry_audit.py
Exit: 0 all verified/declared; 1 drift found; 2 usage.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "TOOLS.md")
ROUTER = os.path.join(ROOT, "AGENTS.md")
SKIP_TREES = ("RE_output/", "RE_build/")
TOOL_EXTS = (".py", ".sh", ".bash")


def rows_from_tools_md():
    out = []
    for line in open(TOOLS, encoding="utf8"):
        # first cell = script path, optionally followed by an argument spec
        # ("RE_scripts/callers.py <va>", "RE_scripts/boot_outcome.py")
        m = re.match(r"\|\s*(RE_scripts/[^|\s]+)[^|]*\|", line)
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


def declared_tools():
    """RE_scripts tools that declare a # REGISTRY: caps: line -> [(relpath, caps)]."""
    out = []
    scripts = os.path.join(ROOT, "RE_scripts")
    for name in sorted(os.listdir(scripts)):
        if not name.endswith(TOOL_EXTS):
            continue
        rel = "RE_scripts/" + name
        caps = tool_caps(os.path.join(scripts, name))
        if caps is not None:
            out.append((rel, caps))
    return out


def router_tokens():
    """Unique file references in AGENTS.md: [(token, is_pathed)]."""
    try:
        text = open(ROUTER, encoding="utf8", errors="replace").read()
    except OSError:
        return []
    seen, out = set(), []
    for t in re.findall(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|py|sh|json)\b", text):
        if "*" in t or t in seen:
            continue
        seen.add(t)
        out.append((t, "/" in t))
    return out


def basename_index():
    """basename -> first repo path, for resolving bare-name mentions."""
    idx = {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git",)]
        for f in fn:
            idx.setdefault(f, os.path.relpath(os.path.join(dp, f), ROOT))
    return idx


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

    # --- 3. REVERSE ROW CHECK: caps declared but no TOOLS.md row ---
    row_paths = {p for p, _, _ in rows}
    rev_missing = 0
    for rel, caps in declared_tools():
        if rel not in row_paths:
            fails.append("ROW-MISSING: %s declares caps %s but has no TOOLS.md "
                         "row - the registry cannot vouch for it" %
                         (rel, sorted(caps)))
            rev_missing += 1

    # --- 4. ROUTER FILE CHECK (the dump_search class) ---
    tracked = set()
    gl = subprocess.run(["git", "ls-files"], cwd=ROOT,
                        capture_output=True, text=True)
    if gl.returncode == 0:
        tracked = set(gl.stdout.split())
    bidx = basename_index()
    for tok, is_pathed in router_tokens():
        if tok.startswith(SKIP_TREES):
            continue
        if not is_pathed:
            # bare-name mention: resolve via basename index; unresolvable
            # bare names are prose, not drift
            if os.path.basename(tok) not in bidx:
                warns.append("ROUTER BARE-NAME UNRESOLVED: %s" % tok)
            continue
        p = os.path.join(ROOT, tok)
        if not os.path.exists(p):
            fails.append("ROUTER MISSING FILE: %s" % tok)
        elif tracked and tok not in tracked:
            warns.append("ROUTER UNTRACKED: %s (exists but not in git - "
                         "drift until committed)" % tok)

    if warns or fails:
        print("reverse/tree-direction: row-missing %d | router fails %d | "
              "router warns %d" % (
                  rev_missing,
                  sum(1 for f in fails if f.startswith("ROUTER MISSING")),
                  sum(1 for w in warns if w.startswith("ROUTER"))))
    for w in warns:
        if w.startswith("ROUTER"):
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
