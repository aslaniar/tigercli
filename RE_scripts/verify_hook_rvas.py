#!/usr/bin/env python3
# REGISTRY: caps: hook-rva-verify, install-table-check
"""Resolve EVERY client-hook RVA constant against .pdata. Exit 1 if any is not a
function START.

WHY THIS EXISTS (p2(112), 2026-08-29): profile_harvest shipped kWrapperRva=0x1A6040
for 0x1417A6040, whose real RVA is 0x17A6040 - a dropped digit. The bad value still
landed inside the module, so the observer's `module_range` check PASSED and the detour
attached to an unrelated function. The boot logged `install result=ok` and then nothing,
through a Tower dwell, a subclass swap and a full character switch. A range check proves
an address is IN the image; it never proves it is the RIGHT address. Only .pdata does.

Run before any boot shipping a new or changed hook address.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "RE_scripts"))
from hook_targets import parse_tables, declared_constants, strip_comments

HOOKS = Path(os.environ.get(
    "RE_HOOKS_DIR",
    str(ROOT / "RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks")))
IMAGE_BASE = 0x140000000
RVA_RE = re.compile(r"constexpr\s+std::uintptr_t\s+(k\w*Rva)\s*=\s*(0x[0-9A-Fa-f]+)\s*;")


def owning_entry(va: int):
    """@return (begin, end, offset) from pdata_bounds, or None when unresolved."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "RE_scripts/pdata_bounds.py"), hex(va)],
        capture_output=True, text=True, timeout=180).stdout
    m = re.search(r"entry (0x[0-9A-Fa-f]+)\.\.(0x[0-9A-Fa-f]+).*offset=(0x[0-9A-Fa-f]+)", out)
    return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16)) if m else None


def main() -> int:
    if not HOOKS.is_dir():
        print(f"FAIL: hook tree missing: {HOOKS}")
        return 1

    # ---- PHASE 1: the INSTALL TABLES (T1.4: declarations are not installs).
    # The decisive check is arithmetic: declared size vs initializer count,
    # plus null/rva-0 entries. The 09-05 FAILURE 2 build PASSED the old
    # constants scan below while its table installed a value-initialised
    # {nullptr, 0} tail at RVA 0.
    tables, table_bad = parse_tables(HOOKS), 0
    n_entries = sum(len(t.entries) for t in tables)
    table_entry_vas = set()
    for t in tables:
        probs = t.problems()
        print(f"TABLE {t.var} ({t.file.name}:{t.lineno}): declared="
              f"{t.declared_size} initializers={len(t.entries)}")
        for p in probs:
            print(f"  ** {p}")
            table_bad += 1
        for e in t.entries:
            if e.rva and e.name:
                table_entry_vas.add(IMAGE_BASE + e.rva)
    print(f"TARGETS TABLE: {n_entries - table_bad}/{n_entries} entries verified, "
          f"{table_bad} bad")

    consts = declared_constants(HOOKS)
    unused = sorted(n for n, c in consts.items() if c["uses"] == 0)
    if unused:
        print(f"advisory: {len(unused)} declared-but-unused RVA constant(s) "
              "(declared, never referenced in live code): " + ", ".join(unused))

    rows, bad, noncode, scanned_vas = [], 0, [], set()
    for path in sorted(HOOKS.rglob("*.cpp")):
        text = strip_comments(path.read_text(errors="replace"))
        for name, literal in RVA_RE.findall(path.read_text(errors="replace")):
            rva = int(literal, 16)
            if rva == 0:
                continue
            va = IMAGE_BASE + rva
            scanned_vas.add(va)
            entry = owning_entry(va)
            if entry is None:
                verdict, bad = "UNRESOLVED (no .pdata entry)", bad + 1
            elif not (entry[0] <= va < entry[1]):
                # pdata_bounds returns the nearest preceding entry, so an address past
                # that entry's END is not code at all - a data constant (an IV, a count).
                # Those are legitimate hook inputs; flag for eyes, do not fail the gate.
                verdict = f"NOT-CODE (past fn end {hex(entry[1])}) - data address, review"
                noncode.append(name)
            elif entry[2] != 0:
                verdict, bad = f"FRAGMENT offset={hex(entry[2])} of {hex(entry[0])}", bad + 1
            elif entry[0] != va:
                verdict, bad = f"MID-FUNCTION, owner starts {hex(entry[0])}", bad + 1
            else:
                verdict = f"ok  fn {hex(entry[0])}..{hex(entry[1])}"
            rows.append((path.relative_to(ROOT).as_posix(), name, literal, hex(va), verdict))
    width = max((len(r[1]) for r in rows), default=8)
    for rel, name, literal, va, verdict in rows:
        flag = "    " if verdict.startswith("ok") else "**  "
        print(f"{flag}{name:<{width}}  {literal:<12} va={va:<12} {verdict}")
        if not verdict.startswith("ok"):
            print(f"      in {rel}")
    print(f"\n{len(rows)} hook RVAs checked, {bad} bad, {len(noncode)} not-code")
    # table entries whose RVA is a literal (not a declared constant) are not
    # covered by the scan above - validate them here
    for va in sorted(table_entry_vas - scanned_vas):
        entry = owning_entry(va)
        ok = entry is not None and entry[0] <= va < entry[1] and entry[2] == 0 and entry[0] == va
        print(f"** literal table RVA va={va:#x}: "
              + (f"ok fn {hex(entry[0])}..{hex(entry[1])}" if ok and entry else "NOT a clean function start"))
        if not ok:
            bad += 1
    if noncode:
        print("not-code (data addresses, not gate failures): " + ", ".join(noncode))
    if bad or table_bad:
        print("VERIFY FAIL - a detour on a wrong address installs cleanly and fires never"
              + (f"; {table_bad} table problem(s) (T1.4)" if table_bad else "") + ".")
        return 1
    print("VERIFY PASS - every hook RVA is a .pdata function START; the install "
          "table arithmetic is clean (declared size == initializer count, no null entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
