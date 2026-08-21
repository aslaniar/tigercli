"""s2v0_capture.py — the S2-0 live-capture (carrier + schema), run while the game is in the Tower.

The capture plan (claims/s2v0-carrier-spawn.md §1.3/§2.2), all read-only:
  1. type-getter stub bytes @ 0x140E00700 + 0x140DFFFF0 (the B8 imm32 C3 mov-eax;ret
     = the handled type for objects A/B of the 15-object table).
  2. the FULL 15-object table @ 0x141C26E28, 0x30 stride x 15 (the q0s = all the
     type getters; the phase9 dump was truncated at 2).
  3. DAT_14280E3E0[0..58] (8-byte stride) = the per-type state objects (their
     vtable+0x18 = the payload decoder for each type).
  4. the schema tree behind *DAT_142439C70 (the 0x40-stride groups; the row whose
     col1 == n1019's stream pointer 0x22A805FD000 -> its index hash = the
     schemaTagHash).

Usage: arm before the boot (45 min window); latches destiny2.exe, waits until the
schema root is populated, dumps everything to RE_output/content/s2v0_capture.bin
+ s2v0_capture.json, then exits. READ-ONLY (RPM only).
"""
import ctypes
import ctypes.wintypes as wt
import json
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory, find_module_base

ROOT = Path(__file__).resolve().parent.parent
OUT_BIN = ROOT / 'RE_output' / 'content' / 's2v0_capture.bin'
OUT_JSON = ROOT / 'RE_output' / 'content' / 's2v0_capture.json'

KNOWN_BASE = 0x7FF641BF0000
IMG = 0x140000000


def va(image_va):
    return KNOWN_BASE + (image_va - IMG)




def ts():
    return time.strftime('%H:%M:%S')


def main():
    print(f'[{ts()}] s2v0 capture armed (base 0x{KNOWN_BASE:X}, arm 45 min)')
    deadline = time.time() + 2700
    handled = set()
    while time.time() < deadline:
        pid = find_pid('destiny2.exe')
        if pid and pid not in handled:
            handled.add(pid)
            try:
                h = open_process(pid)
            except Exception as e:
                print(f'[{ts()}] open failed: {e}')
                continue
            try:
                mb = 0
                for _ in range(30):
                    try:
                        mb = find_module_base(pid, 'destiny2.exe')
                        if mb:
                            break
                    except Exception:
                        pass
                    time.sleep(0.2)
                print(f'[{ts()}] pid {pid} base 0x{mb:X} (KNOWN_BASE 0x{KNOWN_BASE:X})')
                if not mb:
                    print(f'[{ts()}] base unresolvable -> abort (safety)')
                    continue
                if mb != KNOWN_BASE:
                    print(f'[{ts()}] WARNING: base re-rolled; using the LIVE base 0x{mb:X}')
                # verify the base: the MZ header must read
                try:
                    mz = read_memory(h, mb, 2)
                    if mz != b'MZ':
                        print(f'[{ts()}] base sanity failed ({mz.hex()}) -> abort')
                        continue
                except Exception as e:
                    print(f'[{ts()}] base sanity read failed: {e} -> abort')
                    continue
                def va_live(image_va):
                    return mb + (image_va - IMG)
                TARGETS = {
                    "stub_A": (va_live(0x140E00700), 16),
                    "stub_B": (va_live(0x140DFFFF0), 32),
                    "obj_table": (va_live(0x141C26E28), 0x2D0),
                    "state_table": (va_live(0x14280E3E0), 59 * 8),
                }
                frames = {}
                # wait for the schema root to be populated (the destination load)
                root = None
                for _ in range(600):
                    try:
                        d = read_memory(h, va_live(0x142439C70), 8)
                        root = struct.unpack('<Q', d)[0] if d and len(d) == 8 else 0
                    except Exception:
                        root = 0
                    if root and 0x10000000000 < root < 0x7FFFFFFFFFFF:
                        break
                    time.sleep(0.5)
                print(f'[{ts()}] schema root: {root:#x}')
                for name, (addr, size) in TARGETS.items():
                    try:
                        d = read_memory(h, addr, size)
                    except Exception as e:
                        d = None
                        print(f'[{ts()}] {name}: read failed {e}')
                    if d:
                        frames[name] = d.hex()
                        print(f'[{ts()}] {name} @{addr:#x}: {d[:24].hex()}')
                # schema tree: root group + the first 24 groups (0x40 stride), 0x60 each
                if root:
                    try:
                        d = read_memory(h, root, 0x40 * 24)
                        frames['schema_groups'] = d.hex()
                        print(f'[{ts()}] schema groups @{root:#x}: {len(d)} B')
                    except Exception as e:
                        print(f'[{ts()}] schema groups read failed: {e}')
                # decode the stubs (B8 imm32 C3 = mov eax,imm; ret)
                for name in ('stub_A', 'stub_B'):
                    if name in frames:
                        b = bytes.fromhex(frames[name])
                        if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
                            typ = struct.unpack_from('<I', b, 1)[0]
                            print(f'[{ts()}] {name} -> type {typ} ({typ if typ < 59 else "??"})')
                # the obj table q0s
                if 'obj_table' in frames:
                    t = bytes.fromhex(frames['obj_table'])
                    q0s = [struct.unpack_from('<Q', t, i * 0x30)[0] for i in range(15)]
                    print(f'[{ts()}] 15 q0 type getters: {[hex(q) for q in q0s]}')
                OUT_BIN.write_bytes(b''.join(bytes.fromhex(v) for v in frames.values()))
                OUT_JSON.write_text(json.dumps({'pid': pid, 'root': hex(root) if root else None,
                                                'targets': {k: v for k, v in frames.items()}},
                                               indent=1), encoding='utf-8')
                print(f'[{ts()}] capture saved')
            finally:
                import ctypes as _c
                try:
                    _c.WinDLL('kernel32').CloseHandle(h)
                except Exception:
                    pass
        time.sleep(0.2)
    print(f'[{ts()}] window closed')


if __name__ == '__main__':
    main()
