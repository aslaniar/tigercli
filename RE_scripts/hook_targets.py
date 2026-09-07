#!/usr/bin/env python3
# REGISTRY: caps: hook-targets-parse
"""hook_targets.py - parse the client's INSTALL TARGET TABLES (the source of
truth for what actually gets detoured), shared by verify_hook_rvas.py and
preflight.py.

WHY THIS EXISTS (TOOLING_AUDIT T1.4): verify_hook_rvas.py scanned DECLARED
`constexpr ... k*Rva` CONSTANTS - not the table that actually gets installed.
It therefore PASSED a build whose hook table had one entry fewer than its
declared size: std::array VALUE-INITIALISES the missing element into
{name=nullptr, rva=0}, the installer detoured RVA 0 into the PE header, and
the client crashed at login. The constants scan never saw the absent entry
(it does not exist in source) and the gate that exists to catch bad hook
addresses missed the worst hook-address bug of the 09-05 session.

The decisive check is arithmetic, and it lives here: DECLARED SIZE vs
INITIALIZER COUNT. A table with fewer initializers than its size constant
has a value-initialised tail - that IS the crash, visible in source.

API:
  parse_tables(hooks_dir)  -> [Table]
      Table: file, var, declared_size (int|None), entries [Entry]
      Entry: name (str|None for nullptr), rva_expr (str), rva (int|None),
             lineno
  declared_constants(hooks_dir) -> {name: {"value": int, "file": Path,
      "lineno": int, "uses": int}}   # uses = occurrences beyond its own decl

Entry shapes handled: {"name", kXRva, ...} | {"name", 0xN, ...} |
{nullptr, ...}. The rva expression is RESOLVED against the constexpr map;
unresolvable expressions surface as rva=None (the caller decides).
"""
import re
from pathlib import Path

ARRAY_RE = re.compile(
    r"constexpr\s+std::array<\s*Target\s*,\s*(\w+)\s*>\s+(\w+)\s*\{\{(.*?)\}\};",
    re.S)
SIZE_RE = re.compile(r"constexpr\s+std::size_t\s+(\w+)\s*=\s*(\d+)\s*;")
ENTRY_RE = re.compile(
    r'\{\s*(nullptr|&?[\w:]+|"[^"]*")\s*,\s*(nullptr|0x[0-9A-Fa-f]+|[kK]\w+|\d+)\s*,')
CONST_RE = re.compile(
    r"constexpr\s+std::uintptr_t\s+(k\w*Rva)\s*=\s*(0x[0-9A-Fa-f]+)\s*;")


def strip_comments(text):
    """Remove // and /* */ comments while PRESERVING line structure and string
    literals. Without this, a commented-out table entry (the retired image_set
    row) is counted as live - a false 48-vs-47 mismatch that would fail a good
    build. The parser must read what the COMPILER reads."""
    out = []
    for line in text.split("\n"):
        res, in_str, i = [], False, 0
        while i < len(line):
            c = line[i]
            if in_str:
                if c == "\\" and i + 1 < len(line):
                    res.append(line[i:i + 2]); i += 2; continue
                if c == '"':
                    in_str = False
                res.append(c)
            elif c == '"':
                in_str = True
                res.append(c)
            elif line[i:i + 2] == "//":
                break
            elif line[i:i + 2] == "/*":
                j = line.find("*/", i + 2)
                i = (j + 2) if j >= 0 else len(line)
                continue
            else:
                res.append(c)
            i += 1
        out.append("".join(res))
    return "\n".join(out)


class Entry:
    __slots__ = ("name", "rva_expr", "rva", "lineno", "kind")

    def __init__(self, name, rva_expr, rva, lineno, kind=None):
        self.name, self.rva_expr, self.rva, self.lineno = name, rva_expr, rva, lineno
        self.kind = kind

    def is_null(self):
        return self.name is None or self.rva == 0


class Table:
    __slots__ = ("file", "var", "declared_size", "entries", "lineno")

    def __init__(self, file, var, declared_size, entries, lineno):
        self.file, self.var, self.declared_size = file, var, declared_size
        self.entries, self.lineno = entries, lineno

    def problems(self):
        """The arithmetic + null checks. @return [str] (empty = clean)."""
        out = []
        n_decl = self.declared_size
        n_init = len(self.entries)
        if n_decl is not None and n_init != n_decl:
            out.append(
                f"{self.file.name}:{self.lineno}: {self.var} declares "
                f"{n_decl} but the initializer has {n_init} entries - the "
                "tail would be VALUE-INITIALISED to {name=nullptr, rva=0} "
                "and the installer would detour RVA 0 (09-05 FAILURE 2)")
        for e in self.entries:
            if e.name is None:
                out.append(f"{self.file.name}:{e.lineno}: entry name is "
                           "nullptr - would install a nameless hook")
            if e.rva == 0:
                out.append(f"{self.file.name}:{e.lineno}: entry "
                           f"{e.name!r} has rva==0 - would detour RVA 0 "
                           "(the PE header)")
            if e.rva is None:
                out.append(f"{self.file.name}:{e.lineno}: entry {e.name!r} "
                           f"rva expression {e.rva_expr!r} UNRESOLVED - the "
                           "tool cannot vouch for it")
        return out


def duplicate_rva_problems(tables):
    """CROSS-TABLE duplicate-RVA reject (09-06 BLIND-GUARD DEFECT 4:
    walk_leave shipped as a SECOND row on the SAME RVA as walk_map - dual
    detours on one function start are an unsupported install; the rig client
    froze mid-hot-path and the frozen process held the DLL hostage. The
    per-table problems() cannot see across rows; this check can)."""
def duplicate_rva_problems(tables, raw_reader=None):
    """CROSS-TABLE duplicate-RVA reject (09-06 BLIND-GUARD DEFECT 4:
    walk_leave shipped as a SECOND row on the SAME RVA as walk_map - dual
    detours on one function start are an unsupported install; the rig client
    froze mid-hot-path and the frozen process held the DLL hostage. The
    per-table problems() cannot see across rows; this check can).

    A duplicate is a FAILURE unless one of the duplicate rows carries a
    machine-readable waiver `DUAL-OK: <reason>` in its raw source (read
    WITH comments - the waiver is a citation, like no-leave:). The pool_*
    pairs predate the incident and run dual-detoured on COLD paths; they
    must say so in source, not rely on a reader's memory."""
    seen = {}
    out = []
    for t in tables:
        for e in t.entries:
            if e.rva in (None, 0) or e.name is None:
                continue
            seen.setdefault(e.rva, []).append((t, e))
    for rva, rows in sorted(seen.items()):
        if len(rows) < 2:
            continue
        waived = False
        for t, e in rows:
            if raw_reader:
                raw = raw_reader(t.file, e.lineno)
                if "DUAL-OK:" in raw:
                    waived = True
        if waived:
            continue
        where = ", ".join(f"{t.var}:{e.name!r} ({t.file.name}:{e.lineno})"
                          for t, e in rows)
        out.append(f"DUPLICATE RVA {hex(rva)}: {len(rows)} rows target the "
                   f"same function start ({where}) - dual detours on one "
                   "function start are an UNSUPPORTED install (09-06 "
                   "DEFECT 4); route enter+leave through one row's dispatch, "
                   "or waive in source with 'DUAL-OK: <reason>' on the row")
    return out


def raw_lines_around(path, lineno, span=1):
    """Raw (unstripped) source lines around a table row - the DUAL-OK: /
    no-leave: waiver citations live in COMMENTS, which strip_comments drops,
    so waiver checks read the raw file by line number."""
    try:
        lines = Path(path).read_text(errors="replace").split("\n")
    except OSError:
        return ""
    lo = max(0, lineno - 1 - span)
    return "\n".join(lines[lo:lineno - 1 + span + 1])


def declared_constants(hooks_dir):
    """Every `constexpr std::uintptr_t k*Rva = 0x...;` under hooks_dir, with
    a use count (occurrences of the identifier beyond its own declaration)."""
    out = {}
    for path in sorted(Path(hooks_dir).rglob("*.cpp")):
        text = strip_comments(path.read_text(errors="replace"))
        for m in CONST_RE.finditer(text):
            name = m.group(1)
            uses = text.count(name) - 1  # its own declaration line
            out[name] = {"value": int(m.group(2), 16), "file": path,
                         "lineno": text[:m.start()].count("\n") + 1,
                         "uses": uses}
    return out


def parse_tables(hooks_dir):
    """Every `constexpr std::array<Target, N> var{{...}};` under hooks_dir."""
    consts = declared_constants(hooks_dir)
    tables = []
    for path in sorted(Path(hooks_dir).rglob("*.cpp")):
        text = strip_comments(path.read_text(errors="replace"))
        sizes = {m.group(1): int(m.group(2)) for m in SIZE_RE.finditer(text)}
        for m in ARRAY_RE.finditer(text):
            size_var, var, body = m.group(1), m.group(2), m.group(3)
            lineno = text[:m.start()].count("\n") + 1
            entries = []
            entry_spans = list(ENTRY_RE.finditer(body))
            for idx, em in enumerate(entry_spans):
                name_tok, rva_tok = em.group(1), em.group(2)
                name = None if name_tok == "nullptr" else name_tok.strip('"')
                if rva_tok == "nullptr" or rva_tok == "0":
                    rva = 0
                elif rva_tok.lower().startswith("0x"):
                    rva = int(rva_tok, 16)
                elif rva_tok in consts:
                    rva = consts[rva_tok]["value"]
                else:
                    rva = None
                # the row's Probe::kind (its dispatch class - the enum's doc
                # comments declare which kinds observe the OUTCOME, which is
                # what the enter/leave pairing audit needs)
                row_end = (entry_spans[idx + 1].start()
                           if idx + 1 < len(entry_spans) else len(body))
                km = re.search(r"Probe::(\w+)", body[em.start():row_end])
                kind = km.group(1) if km else None
                entries.append(Entry(name, rva_tok, rva,
                                     lineno + body[:em.start()].count("\n"),
                                     kind))
            tables.append(Table(path, var, sizes.get(size_var), entries, lineno))
    return tables


if __name__ == "__main__":
    import sys
    hooks = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(__file__).resolve().parent.parent / \
        "RE_build/Sunrise-fork-inventory/Sunrise/src/client/hooks"
    consts = declared_constants(hooks)
    print(f"declared k*Rva constants: {len(consts)}")
    unused = [n for n, c in consts.items() if c["uses"] == 0]
    print(f"declared-but-unused (advisory): {len(unused)}")
    tables = parse_tables(hooks)
    for t in tables:
        print(f"table {t.var} in {t.file.name}:{t.lineno}: declared="
              f"{t.declared_size} initializers={len(t.entries)}")
        for p in t.problems():
            print(f"  PROBLEM {p}")
    for p in duplicate_rva_problems(
            tables,
            raw_reader=lambda path, lineno: raw_lines_around(path, lineno)):
        print(f"  PROBLEM {p}")
    print("parse ok" if tables else "NO TABLES FOUND")
