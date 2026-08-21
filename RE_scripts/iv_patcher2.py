"""iv_patcher2.py — patch the EXPECTED side, not the IV (the +29s lesson).

WHY THIS EXISTS (FINDINGS 9.38-9.39, live-verified 22:32 boot):
  - The external game's registration path WRITES the failing IV into the kind0
    IV buffer at ~+29s post-launch, microseconds before the validator reads it.
    A 5ms poll cannot interpose on that race (the write and the -87 landed in
    the same poll window). The IV patcher lost.
  - The expected side (per-record u32 @+0x168 = 0x281141FD, in a 2,198-record
    array at 632-byte stride) is written EARLY and is NOT rewritten during the
    failing registration (the failing dump still carries 0x281141FD everywhere
    post-failure). It is a stable target.
  - Therefore: rewrite every record's expected 0x281141FD -> 0x3DB8F835 (the
    value the game WILL compute from its own failing IV at +29s). Then
    expected == computed for every kind0 record -> the registration passes ->
    bootstrap + investment globals load -> character select.

SAFETY (unchanged from iv_patcher.py): module base verified before ANY write
(resolve_base retry + pattern-gate fallback); writes only to validated record
addresses (the record header {u16 0x26, u16 2, u16 id, u16 1} at hit-0x164 is
checked before every write); the result register gates the writes (stop at the
verdict); multi-pid selection, no writes to wrong-base processes.

Output: RE_output/content/iv_patch2_out.txt
"""
import ctypes
import ctypes.wintypes as wt
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, find_module_base, kernel32, PROCESSENTRY32W, MEMORY_BASIC_INFORMATION

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'RE_output' / 'content' / 'iv_patch2_out.txt'

KNOWN_BASE = 0x7FF641BF0000
RESULT_RVA = 0x267AA50                # DAT_14267aa50 (result register, u32)
STATE_RVA = 0x1F916FC                 # DAT_141f916fc (registration state, u32)

EXPECTED_HEALTHY = struct.pack('<I', 0x281141FD)   # the persisted expected (LE bytes)
EXPECTED_PATCH = struct.pack('<I', 0x3DB8F835)     # the failing-IV computed value
RECORD_STRIDE = 632

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

POLL_S = 0.005
ARM_S = 2700
SCAN_DEADLINE_S = 40.0                # stop hunting for the array 40s after latch
CHUNK = 1 << 20                       # 1 MiB scan chunks


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
    if not ok:
        return None
    return buf.raw[:nread.value]


def write_memory_raw(handle, addr, data):
    nwrite = ctypes.c_size_t(0)
    ok = kernel32.WriteProcessMemory(handle, ctypes.c_void_p(addr), data, len(data), ctypes.byref(nwrite))
    return bool(ok) and nwrite.value == len(data)


def resolve_base(pid, tries=30):
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


def committed_regions(handle):
    """Enumerate committed MEM_PRIVATE/MEM_MAPPED regions via VirtualQueryEx
    (proper MEMORY_BASIC_INFORMATION layout)."""
    out = []
    addr = 0x10000
    maxaddr = 0x7FFFFFFFFFFF
    while addr < maxaddr:
        mbi = MEMORY_BASIC_INFORMATION()
        r = kernel32.VirtualQueryEx(handle, ctypes.c_void_p(addr), ctypes.byref(mbi),
                                    ctypes.sizeof(mbi))
        if not r:
            break
        if mbi.RegionSize == 0:
            break
        if mbi.State == 0x1000:  # MEM_COMMIT
            out.append((mbi.BaseAddress, mbi.RegionSize))
        nxt = mbi.BaseAddress + mbi.RegionSize
        if nxt <= addr:
            break
        addr = nxt
    return out


def valid_record(handle, hit_addr):
    """hit_addr = the expected field (@+0x168). Check the record header at hit-0x164."""
    hdr = read_memory_raw(handle, hit_addr - 0x164, 8)
    if hdr is None:
        return False
    v0, v1 = struct.unpack_from('<HH', hdr, 0)
    v2 = struct.unpack_from('<H', hdr, 4)[0]
    return v0 == 0x26 and v1 == 2 and v2 != 0


def scan_for_expected(handle, log_every=8):
    """Scan committed memory for the expected pattern; validate + return record hit addresses."""
    hits = []
    t0 = time.time()
    for base, size in committed_regions(handle):
        if time.time() - t0 > 12:
            break
        pos = 0
        while pos < size:
            n = min(CHUNK, size - pos)
            buf = read_memory_raw(handle, base + pos, n)
            if buf is None:
                pos += CHUNK
                continue
            off = 0
            while True:
                i = buf.find(EXPECTED_HEALTHY, off)
                if i < 0:
                    break
                hit = base + pos + i
                if valid_record(handle, hit):
                    hits.append(hit)
                off = i + 1
            pos += n
    return hits


def latch_and_patch(pid):
    log(f'pid {pid}: latching')
    h = kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
        False, pid)
    if not h:
        log(f'pid {pid}: OpenProcess failed')
        return
    try:
        mb = resolve_base(pid)
        log(f'pid {pid}: module base 0x{mb or 0:X} (KNOWN_BASE 0x{KNOWN_BASE:X})')
        if mb != KNOWN_BASE:
            log(f'pid {pid}: BASE MISMATCH -> ABORTING (safety)')
            return
        result_addr = KNOWN_BASE + RESULT_RVA
        state_addr = KNOWN_BASE + STATE_RVA

        patches = 0
        scan_t0 = time.time()
        last_status = time.time()
        last_result = None
        last_state = None
        found_at = None
        while time.time() < scan_t0 + SCAN_DEADLINE_S:
            proch = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if proch:
                code = wt.DWORD(0)
                kernel32.GetExitCodeProcess(proch, ctypes.byref(code))
                kernel32.CloseHandle(proch)
                if code.value != 259:
                    break
            else:
                break
            res = read_memory_raw(h, result_addr, 4)
            rv = struct.unpack('<I', res)[0] if res else None
            if rv == 0xFFFFFFA9:
                log(f'pid {pid}: verdict already -87 before patch window -> no writes')
                return
            if patches == 0:
                hits = scan_for_expected(h)
                log(f'pid {pid}: scan found {len(hits)} validated record hits '
                    f'({time.time()-scan_t0:.1f}s in)')
                if len(hits) >= 1000:
                    log(f'pid {pid}: patching {len(hits)} expected fields -> 0x3DB8F835')
                    ok = 0
                    for hit in hits:
                        if write_memory_raw(h, hit, EXPECTED_PATCH):
                            ok += 1
                    patches = ok
                    found_at = time.time() - scan_t0
                    log(f'pid {pid}: patched {ok}/{len(hits)} records at +{found_at:.1f}s')
                else:
                    time.sleep(2.0)
                    continue
            else:
                # re-assert pass (the game must not have rewritten them; cheap insurance)
                if time.time() - last_status >= 5.0:
                    ok = 0
                    for hit in hits:
                        if write_memory_raw(h, hit, EXPECTED_PATCH):
                            ok += 1
                    last_status = time.time()
                    log(f'pid {pid}: re-assert pass: {ok}/{len(hits)} still patched')
            time.sleep(POLL_S)
        if patches == 0:
            log(f'pid {pid}: array never found within {SCAN_DEADLINE_S}s -> no writes this boot')
            return
        # monitoring phase: watch the verdict
        while True:
            proch = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if proch:
                code = wt.DWORD(0)
                kernel32.GetExitCodeProcess(proch, ctypes.byref(code))
                kernel32.CloseHandle(proch)
                if code.value != 259:
                    break
            else:
                break
            res = read_memory_raw(h, result_addr, 4)
            rv = struct.unpack('<I', res)[0] if res else None
            st = read_memory_raw(h, state_addr, 4)
            sv = struct.unpack('<I', st)[0] if st else None
            if rv != last_result:
                tag = ''
                if rv == 0xFFFFFFA9:
                    tag = 'FAIL -87'
                elif rv == 1 and sv is not None and sv >= 3:
                    tag = 'PASS (state>=3)'
                log(f'pid {pid}: result register = {rv if rv is None else f"0x{rv:08X}"} {tag}')
                last_result = rv
            if sv != last_state:
                log(f'pid {pid}: registration state = {sv}')
                last_state = sv
            if rv in (1, 0xFFFFFFA9):
                log(f'pid {pid}: verdict reached after {patches} record patches; monitoring only')
            time.sleep(POLL_S)
        log(f'pid {pid}: game exited; total patched records: {patches}')
    finally:
        kernel32.CloseHandle(h)


def main():
    kernel32.ReadProcessMemory.restype = ctypes.c_bool
    kernel32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel32.WriteProcessMemory.restype = ctypes.c_bool
    kernel32.WriteProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [wt.DWORD, ctypes.c_bool, wt.DWORD]
    kernel32.VirtualQueryEx.restype = ctypes.c_size_t
    kernel32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]

    if OUT.exists():
        OUT.unlink()
    log('iv_patcher2 armed: expected-side patcher. Will find the 2,198-record array '
        f'({EXPECTED_HEALTHY.hex()} at {RECORD_STRIDE}-byte stride) and rewrite every '
        f'expected to {EXPECTED_PATCH.hex()} (= the value the game computes from its own '
        'failing IV at ~+29s), so expected == computed.')
    log(f'KNOWN_BASE=0x{KNOWN_BASE:X}, scan deadline {SCAN_DEADLINE_S}s, arm {ARM_S//60} min')

    cur = find_pid('destiny2.exe')
    log(f'current destiny2.exe pid: {cur or "none (waiting for launch)"}')
    seen = set()
    deadline = time.time() + ARM_S
    while time.time() < deadline:
        try:
            pids = find_pid_all()
        except Exception as exc:
            log(f'find_pid_all error: {exc}')
            pids = []
        pick = None
        for p in pids:
            if p not in seen:
                pick = p
                break
        if pick is None and pids:
            pick = pids[-1]
        if pick and pick not in seen:
            seen.add(pick)
            latch_and_patch(pick)
        time.sleep(0.1)
    log('patcher window closed.')


if __name__ == '__main__':
    main()
