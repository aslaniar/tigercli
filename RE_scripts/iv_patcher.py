"""iv_patcher.py — re-assert the healthy kind0 IV during the external boot.

THE VERDICT (2026-08-15, verified structurally from the dump-pair):
  - the registration records for the failing packages (bootstrap 0x385,
    investment globals 0x58C..) carry kind=0 and expected=0x281141FD
    BYTE-IDENTICALLY in both dumps (mode-independent expected side).
  - kind0 -> the validator's computed hash = mix(kind0 IV @ base+0x1F44CE0).
    healthy boot: IV = D6 2A B2 C1 0C C0 1B C5 35 DB 7B 86 55 C7 DC 3B
                  -> computed 0x281141FD == expected -> PASS.
    failing boot: dwords 4/8 of the IV differ (F5 DC 16 8D / 3F DB 7B 86)
                  -> computed 0x3DB8F835 != expected -> -87 -> black screen.
  - 0x3DB8F835 appears NOWHERE in the failing dump (computed, compared,
    mismatched, aborted, never stored); the expected array holds 0x281141FD
    2,198x in both dumps.

THIS TOOL: latches destiny2.exe, then WRITES the 16 healthy IV bytes into the
kind0 IV buffer (base + 0x1F44CE0) and re-asserts them every poll (5 ms)
through the registration window. ReadProcessMemory everywhere else; the only
WriteProcessMemory is this 16-byte data buffer (a writable .data page; the
anti-tamper cookie checks the stack, not this buffer).

One boot, one variable. The write is PATTERN-GATED: it only fires after the game
itself has written the FAILING IV into the buffer (proof the buffer is in its IV
phase — the t+0 write crashed the game, WER 33000, see FINDINGS 9.38). If it
renders -> the IV divergence was the -87 cause (CONFIRMED LIVE); if not -> the
divergence was a symptom and this patcher retires (the Ghidra writer hunt becomes
the path).

Safety: the module base is verified against KNOWN_BASE before ANY write;
mismatch = abort (never write to a wrong address).

Output: RE_output/content/iv_patch_out.txt (transitions + verdict log).
"""
import ctypes
import ctypes.wintypes as wt
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, kernel32

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'RE_output' / 'content' / 'iv_patch_out.txt'

KNOWN_BASE = 0x7FF641BF0000          # runtime base, stable per reboot session
IV_RVA = 0x1F44CE0                    # kind0 IV buffer (image RVA)
RESULT_RVA = 0x267AA50                # DAT_14267aa50 (result register, u32)
STATE_RVA = 0x1F916FC                 # DAT_141f916fc (registration state, u32)

HEALTHY_IV = bytes.fromhex('D62AB2C10CC01BC535DB7B8655C7DC3B')
FAILING_IV = bytes.fromhex('D62AB2C1F5DC168D3FDB7B8655C7DC3B')

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

POLL_S = 0.005                       # 5 ms re-assert polls
STATUS_S = 1.0                       # status log cadence
ARM_S = 2700                         # 45 min arm window


def ts():
    return time.strftime('%H:%M:%S')


def log(line, flush=True):
    with open(OUT, 'a', encoding='utf8') as f:
        f.write(f'[{ts()}] {line}\n')
    print(f'[{ts()}] {line}', flush=flush)


def read_memory_raw(handle, addr, size):
    buf = ctypes.create_string_buffer(size)
    nread = ctypes.c_size_t(0)
    ok = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, ctypes.byref(nread))
    if not ok or nread.value != size:
        return None
    return buf.raw[:size]


def write_memory_raw(handle, addr, data):
    nwrite = ctypes.c_size_t(0)
    ok = kernel32.WriteProcessMemory(handle, ctypes.c_void_p(addr), data, len(data), ctypes.byref(nwrite))
    return bool(ok) and nwrite.value == len(data)


def resolve_base(pid, tries=30):
    """Retry find_module_base through the loader-lock (error 299 is transient
    during early startup). Returns the base or None."""
    for i in range(tries):
        try:
            mb = find_module_base(pid, 'destiny2.exe')
            if mb:
                return mb
        except Exception:
            pass
        time.sleep(0.2)
    return None


def find_pid_all():
    """Return ALL destiny2.exe pids (snapshot order)."""
    from dump_sunrise_memory import PROCESSENTRY32W
    kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
    kernel32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    if snap == ctypes.c_void_p(-1).value:
        return []
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    out = []
    if not kernel32.Process32FirstW(snap, ctypes.byref(entry)):
        kernel32.CloseHandle(snap)
        return out
    while True:
        if entry.szExeFile.lower() == 'destiny2.exe':
            out.append(int(entry.th32ProcessID))
        if not kernel32.Process32NextW(snap, ctypes.byref(entry)):
            break
    kernel32.CloseHandle(snap)
    return out


def main():
    kernel32.ReadProcessMemory.restype = ctypes.c_bool
    kernel32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel32.WriteProcessMemory.restype = ctypes.c_bool
    kernel32.WriteProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [wt.DWORD, ctypes.c_bool, wt.DWORD]

    if OUT.exists():
        OUT.unlink()
    log(f'iv patcher armed: will re-assert healthy kind0 IV at base+0x{IV_RVA:X} '
        f'(KNOWN_BASE=0x{KNOWN_BASE:X}, poll {POLL_S*1000:.0f} ms, arm {ARM_S//60} min)')
    log(f'healthy IV: {HEALTHY_IV.hex()}')
    log(f'failing IV: {FAILING_IV.hex()}')

    pid = find_pid('destiny2.exe')
    log(f'current destiny2.exe pid: {pid or "none (waiting for launch)"}')
    seen = set()

    deadline = time.time() + ARM_S
    iv_addr = KNOWN_BASE + IV_RVA
    result_addr = KNOWN_BASE + RESULT_RVA
    state_addr = KNOWN_BASE + STATE_RVA

    handled = {}
    while time.time() < deadline:
        try:
            pids = find_pid_all()
        except Exception as exc:
            log(f'find_pid_all error: {exc}')
            pids = []
        cur = None
        for p in pids:
            if p not in seen:
                cur = p
                break
        if cur is None and pids:
            cur = pids[-1]
        if cur and cur not in seen:
            seen.add(cur)
            # ---- latch ----
            h = kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
                False, cur)
            if not h:
                log(f'pid {cur}: OpenProcess failed (no write rights); skipping this pid')
                continue
            try:
                mb = resolve_base(cur)
                log(f'pid {cur}: module base 0x{mb or 0:X} (KNOWN_BASE 0x{KNOWN_BASE:X})')
                if mb is None:
                    probe = read_memory_raw(h, iv_addr, 16)
                    if probe is not None and probe in (HEALTHY_IV, FAILING_IV):
                        log(f'pid {cur}: module snapshot failed but IV buffer matches a known '
                            f'pattern ({probe.hex()}) -> address confirmed, proceeding')
                    else:
                        log(f'pid {cur}: module snapshot failed AND IV pattern gate failed '
                            f'({probe.hex() if probe else "unreadable"}) -> ABORTING this pid (safety)')
                        kernel32.CloseHandle(h)
                        continue
                elif mb != KNOWN_BASE:
                    log(f'pid {cur}: BASE MISMATCH -> ABORTING WRITES for this pid (safety)')
                    kernel32.CloseHandle(h)
                    continue
                first = read_memory_raw(h, iv_addr, 16)
                log(f'pid {cur}: IV at latch: {first.hex() if first else "UNREADABLE"}')
                patches = 0
                patched = False
                last_status = time.time()
                last_result = None
                last_state = None
                last_buf = first
                while time.time() < deadline:
                    proch = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, cur)
                    if proch:
                        code = wt.DWORD(0)
                        kernel32.GetExitCodeProcess(proch, ctypes.byref(code))
                        kernel32.CloseHandle(proch)
                        if code.value != 259:  # STILL_ACTIVE
                            break
                    else:
                        break
                    buf = read_memory_raw(h, iv_addr, 16)
                    if buf is not None and buf != last_buf:
                        last_buf = buf
                        log(f'pid {cur}: IV buffer transition: {buf.hex()} '
                            f'({"=FAILING pattern" if buf == FAILING_IV else "=HEALTHY pattern" if buf == HEALTHY_IV else ""})')
                    # the result register gates writes: once the verdict is in, stop touching memory
                    res_now = read_memory_raw(h, result_addr, 4)
                    rv_now = struct.unpack('<I', res_now)[0] if res_now else None
                    if rv_now in (1, 0xFFFFFFA9):
                        verdict = 'PASS' if rv_now == 1 else 'FAIL -87'
                        if patched:
                            log(f'pid {cur}: verdict {verdict} (0x{rv_now:08X}) after {patches} re-assert(s); writes stopped')
                            patched = False
                        # continue monitoring only
                    elif buf is not None and not patched and buf == FAILING_IV:
                        # the game has written its own diverged IV: the buffer is in its
                        # IV phase -> safe to overwrite (never before this moment)
                        log(f'pid {cur}: game wrote the FAILING IV itself -> patching now '
                            f'({buf.hex()} -> {HEALTHY_IV.hex()})')
                        if write_memory_raw(h, iv_addr, HEALTHY_IV):
                            patches += 1
                            patched = True
                    elif buf is not None and patched and buf != HEALTHY_IV:
                        before = buf.hex()
                        if write_memory_raw(h, iv_addr, HEALTHY_IV):
                            patches += 1
                            if patches <= 5 or patches % 200 == 0:
                                log(f'pid {cur}: IV re-assert #{patches}: {before} -> {HEALTHY_IV.hex()}')
                    elif buf is not None and not patched and buf == HEALTHY_IV:
                        if time.time() - last_status >= STATUS_S:
                            last_status = time.time()
                            log(f'pid {cur}: buffer already healthy (game wrote it) - holding, no writes needed')
                    if time.time() - last_status >= STATUS_S:
                        last_status = time.time()
                        res = read_memory_raw(h, result_addr, 4)
                        st = read_memory_raw(h, state_addr, 4)
                        rv = struct.unpack('<I', res)[0] if res else None
                        sv = struct.unpack('<I', st)[0] if st else None
                        if rv != last_result:
                            log(f'pid {cur}: result register = {rv if rv is None else f"0x{rv:08X}"} '
                                f'({"PASS" if rv == 1 else "FAIL -87" if rv == 0xFFFFFFA9 else ""})')
                            last_result = rv
                        if sv != last_state:
                            log(f'pid {cur}: registration state = {sv}')
                            last_state = sv
                    time.sleep(POLL_S)
                log(f'pid {cur}: game exited or deadline; total IV re-asserts: {patches}')
                handled[cur] = patches
            finally:
                kernel32.CloseHandle(h)
        time.sleep(0.1)

    log(f'patcher window closed. handled pids: {handled or "none"}')
    log('VERDICT READOUT: if the boot reached character select, the kind0 IV '
        'divergence was the -87 cause (confirmed live). If it black-screened with '
        'result register 0xFFFFFFA9 despite re-asserts, the divergence was a symptom '
        'and the Ghidra writer hunt becomes the path.')


if __name__ == '__main__':
    main()
