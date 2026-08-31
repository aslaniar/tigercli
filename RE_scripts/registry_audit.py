#!/usr/bin/env python3
"""registry_audit.py - verify TOOLS.md registry rows against tool reality.

The 08-31 failure: TOOLS.md described rig_dll_helper.py as a remote-thread
memory reader; its actual CLI is backup|verify (a deploy helper). A wrong
registry row costs a session a wild-goose chase - the registry is only
trustworthy if its rows are periodically checked against the tools.

Check per row:
  1. the named RE_scripts path exists
  2. the tool's docstring/first-40-lines share at least one significant
     word with the row's description (loose - catches gross drift like
     "memory reader" vs "deploy helper", not subtle drift)

Usage: /usr/bin/python3 RE_scripts/registry_audit.py
Exit: 0 all rows plausible; 1 drift/mismatch found; 2 usage.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "TOOLS.md")

STOPWORDS = {"the", "and", "for", "with", "from", "into", "one", "any",
             "all", "run", "runs", "using", "use", "per", "via", "out",
             "off", "its", "it", "a", "an", "to", "of", "in", "on", "by",
             "new", "read", "reads", "print", "prints", "file", "files"}


def sig_words(text):
    words = set(re.findall(r"[a-z_][a-z0-9_]{3,}", text.lower()))
    return words - STOPWORDS


def rows_from_tools_md():
    out = []
    for line in open(TOOLS, encoding="utf8"):
        m = re.match(r"\|\s*(RE_scripts/\S+)\s*\|", line)
        if m:
            out.append((m.group(1), line.strip()))
    return out


def main():
    if not os.path.exists(TOOLS):
        print("ERROR: no TOOLS.md at %s" % TOOLS)
        return 2
    rows = rows_from_tools_md()
    print("registry rows naming RE_scripts tools: %d" % len(rows))
    problems = []
    checked = 0
    for path, line in rows:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            problems.append("MISSING FILE: %s" % path)
            continue
        checked += 1
        try:
            head = open(full, encoding="utf8", errors="replace").read(2400)
        except OSError as exc:
            problems.append("UNREADABLE: %s (%s)" % (path, exc))
            continue
        overlap = sig_words(head) & sig_words(line)
        if not overlap:
            problems.append(
                "DRIFT: %s - row and docstring share no descriptive words"
                % path)
    print("checked: %d exist, %d total rows" % (checked, len(rows)))
    if problems:
        print("REGISTRY DRIFT (%d):" % len(problems))
        for p in problems:
            print("  - %s" % p)
        print("fix the rows or the tools - the registry is the project's "
              "tool memory; a wrong row costs a wild-goose chase (08-31).")
        return 1
    print("REGISTRY AUDIT PASS - every row names an existing tool with a "
          "plausibly matching description")
    return 0


if __name__ == "__main__":
    sys.exit(main())
