"""iv_patcher3.py — patch the heap IV-storage array (the kind0 vs kindN switch).

EVIDENCE (FINDINGS 9.40, dump-pair structural):
  - A 4 x 960-byte heap array (signature 85 f9 11 c0 ac ab fa 20 at +0xB0/+0x23A/
    +0x26C per struct) holds the game's hash-chain IV set: the HEALTHY dump's
    array carries the kind0 IV (count dword @+0x258 = 0xC1B22AD6 + the rest at
    +0x25C..+0x26B); the FAILING dump's array carries the kindN IV (count =
    0x365D4A3A). The array = mode-divergent -> THE ROOT CANDIDATE for the -87.
  - The .data kind0 buffer @0x1F44CE0 gets its (hybrid/failing) value at ~+29s
    from the game's own writer. If that writer derives from this array, patching
    the array to the healthy kind0 IV makes the game write the healthy value.
  - If the +29s buffer value stays hybrid despite the patch -> the writer is
    array-independent and this tool retires (the static writer hunt wins).

SAFETY: the array = stable data in both dumps (unlike the pool-phase .data
buffer); only the count+IV data fields (+0x258..+0x26B) are written, nothing
else. Base verification + header validation per hit; verdict-gated writes;
multi-pid selection. Output: RE_output/content/iv_patch3_out.txt.
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
OUT = ROOT / 'RE_output' / 'content' / 'iv_patch3_out.txt'

KNOWN_BASE = 0x7FF641BF0000
IV_BUFFER_RVA = 0x1F44CE0               # the .data kind0 buffer (watch only)
RESULT_RVA = 0x267AA50                  # result register
STATE_RVA = 0x1F916FC                   # registration state

SIG = bytes.fromhex('85f911c0acabfa20')  # the array signature (at struct +0xB0)
STRUCT_STRIDE = 0x3C0
SIG_OFF = 0xB0                          # SIG position inside the struct
IV_FIELD_OFF = 0x258                    # count dword + IV dwords 4..C live here
COUNT_HEALTHY = struct.pack('<I', 0xC1B22AD6)
IV_TAIL_HEALTHY = bytes.fromhex('0CC01BC535DB7B8655C7DC3B')   # dwords 4..C
HEALTHY_IV = bytes.fromhex('D62AB2C10CC01BC535DB7B8655C7DC3B')

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008

POLL_S = 0.005
ARM_S = 2700
SCAN_DEADLINE_S = 40.0
CHUNK = 1 << 20


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
        if mbi.State == 0x1000:
            out.append((mbi.BaseAddress, mbi.RegionSize))
        nxt = mbi.BaseAddress + mbi.RegionSize
        if nxt <= addr:
            break
        addr = nxt
    return out


def scan_for_array(handle, tcap=12.0):
    """Find struct bases via the SIG at struct+SIG_OFF."""
    bases = []
    t0 = time.time()
    for base, size in committed_regions(handle):
        if time.time() - t0 > tcap:
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
                i = buf.find(SIG, off)
                if i < 0:
                    break
                cand = base + pos + i - SIG_OFF
                if cand & 0x3F == 0 and cand not in bases:
                    bases.append(cand)
                off = i + 1
            pos += n
    return bases


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
        iv_buf_addr = KNOWN_BASE + IV_BUFFER_RVA

        bases = []
        patches = 0
        scan_t0 = time.time()
        last_status = time.time()
        last_buf = None
        last_result = None
        last_state = None
        patched_once = False
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
            if not patched_once:
                if len(bases) < 4:
                    found = scan_for_array(h)
                    for b in found:
                        if b not in bases:
                            bases.append(b)
                # probe neighbors: the 4 structs are contiguous at STRIDE
                if bases and len(bases) < 4:
                    for b in list(bases):
                        for k in range(-2, 7):
                            cand = b + k * STRUCT_STRIDE
                            if cand < 0x10000 or cand in bases:
                                continue
                            probe = read_memory_raw(h, cand + SIG_OFF, 8)
                            if probe is not None and probe[:8] == SIG:
                                bases.append(cand)
                                log(f'pid {pid}: neighbor probe: struct @ {cand:#x} (k={k:+d})')
                    bases = sorted(bases)
                log(f'pid {pid}: scan: {len(bases)} struct bases ({time.time()-scan_t0:.1f}s in)')
                if len(bases) >= 4:
                    ok = 0
                    for s in bases[:8]:
                        field = read_memory_raw(h, s + IV_FIELD_OFF, 20)
                        cur = field.hex() if field else None
                        if write_memory_raw(h, s + IV_FIELD_OFF, COUNT_HEALTHY + IV_TAIL_HEALTHY):
                            ok += 1
                            log(f'pid {pid}: struct {s:#x}: field {cur} -> patched')
                    patches = ok
                    patched_once = True
                    log(f'pid {pid}: patched {ok}/{len(bases[:8])} struct fields at +{time.time()-scan_t0:.1f}s')
                else:
                    time.sleep(1.0)
                    continue
            else:
                if time.time() - last_status >= 5.0:
                    ok = 0
                    for s in bases[:8]:
                        if write_memory_raw(h, s + IV_FIELD_OFF, COUNT_HEALTHY + IV_TAIL_HEALTHY):
                            ok += 1
                    last_status = time.time()
                    log(f'pid {pid}: re-assert: {ok}/{len(bases[:8])} fields healthy')
            # watch the .data buffer + the result register
            buf = read_memory_raw(h, iv_buf_addr, 16)
            if buf is not None and buf != last_buf:
                last_buf = buf
                log(f'pid {pid}: .data IV buffer transition: {buf.hex()} '
                    f'({"=HEALTHY" if buf == HEALTHY_IV else ""})')
            if time.time() - last_status >= 1.0:
                last_status = time.time()
                st = read_memory_raw(h, state_addr, 4)
                sv = struct.unpack('<I', st)[0] if st else None
                if rv != last_result:
                    log(f'pid {pid}: result register = {rv if rv is None else f"0x{rv:08X}"}')
                    last_result = rv
                if sv != last_state:
                    log(f'pid {pid}: registration state = {sv}')
                    last_state = sv
            time.sleep(POLL_S)
        if not patched_once:
            log(f'pid {pid}: array never found within {SCAN_DEADLINE_S}s -> no writes this boot')
            return
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
                log(f'pid {pid}: result register = {rv if rv is None else f"0x{rv:08X}"} '
                    f'({"PASS (state>=3)" if rv == 1 and sv is not None and sv >= 3 else "FAIL -87" if rv == 0xFFFFFFA9 else ""})')
                last_result = rv
            if sv != last_state:
                log(f'pid {pid}: registration state = {sv}')
                last_state = sv
            buf = read_memory_raw(h, iv_buf_addr, 16)
            if buf is not None and buf != last_buf:
                last_buf = buf
                log(f'pid {pid}: .data IV buffer transition: {buf.hex()} '
                    f'({"=HEALTHY" if buf == HEALTHY_IV else ""})')
            time.sleep(POLL_S)
        log(f'pid {pid}: game exited; patched {patches} struct fields')
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
    log('iv_patcher3 armed: heap IV-array patcher. Finds the 4x960B hash-IV array '
        f'via signature {SIG.hex()}, rewrites each struct\'s count+IV field '
        f'({COUNT_HEALTHY.hex()} + {IV_TAIL_HEALTHY.hex()}) to the healthy kind0 IV, '
        'and watches the .data buffer to see what the +29s writer does.')
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
