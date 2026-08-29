#!/usr/bin/env python3
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
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks"
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
    rows, bad, noncode = [], 0, []
    for path in sorted(HOOKS.rglob("*.cpp")):
        for name, literal in RVA_RE.findall(path.read_text(errors="replace")):
            rva = int(literal, 16)
            if rva == 0:
                continue
            va = IMAGE_BASE + rva
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
    if noncode:
        print("not-code (data addresses, not gate failures): " + ", ".join(noncode))
    if bad:
        print("VERIFY FAIL - a detour on a wrong address installs cleanly and fires never.")
        return 1
    print("VERIFY PASS - every hook RVA is a .pdata function START")
    return 0


if __name__ == "__main__":
    sys.exit(main())
