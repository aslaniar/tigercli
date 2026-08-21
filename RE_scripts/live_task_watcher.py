"""live_task_watcher.py — latch the boot registration task list of destiny2.exe.

Reads the linked task list whose head is the global DAT_14241f630 (runtime
VA = base + 0x241f630, base = 0x7FF641BF0000 this session) and dumps the raw
first 0x200 bytes of every distinct task record into
RE_output/content/task_watch_records.bin as concatenated frames:
    { u64 address }{ u16 length }{ bytes }

READ-ONLY on the game (ReadProcessMemory only): never writes to the game,
never suspends threads, never touches game files.

Structural facts pinned from the corpus (RE_output/export/) + the decrypted
image (RE_output/destiny2_unpacked.exe, the live-captured decrypted build):
  * phase_registration4.txt, FUN_140333e70: dispatcher walks the list headed
    by DAT_14241f630; per record it reads the task-type byte at +0x10, a
    ushort at +0x12, u32s at +0x18 and +0x1c, then advances with
    pcVar4 = FUN_14036add0(record); a fresh batch is pulled from
    FUN_140380870(&DAT_14241c000) when the head runs out.
  * NEXT-POINTER OFFSET = +0x00 (VERIFIED): functions.csv lists FUN_14036add0
    as exactly 4 bytes; the decrypted image bytes at RVA 0x36add0 are
    48 8B 01 C3 = "mov rax,[rcx]; ret" - the link is the FIRST qword of the
    task record.  Confirmed live: the 2026-08-15 run walked 2,199 records
    from pid 18400 with a perfect +0x20 address stride (0x20-byte nodes).
    NOTE: the LIVE page at base+0x36add0 read as 0da19858e1aec387 (still
    VMProtect-packed in the running process); the decrypted capture is the
    authoritative source for the stub bytes.
  * NODE SIZE = 0x20 (INFERRED, high confidence): the +0x10 type byte,
    +0x12 ushort, +0x18/+0x1c u32s all fit inside a 0x20-byte node, and the
    live walk stride was exactly 0x20.  (0x200 bytes are still dumped per
    instruction - a superset, overlapping windows, frames are addressed.)
  * phase_registration3.txt, FUN_140381dd0 (validator): receives a 400-byte
    (0x190) record as param_7 - a DIFFERENT struct (the entitlement/package
    table row, stride 400 per phase_registration2.txt), fields at
    +0x04/+0x06/+0x07/+0x08/+0x20/+0xb4/+0x10c/+0x114/+0x164/+0x168/+0x16c;
    all inside the 0x200 dump window.
"""
import ctypes
import struct
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process, read_memory, kernel32, find_module_base

ROOT = Path(__file__).resolve().parent.parent
RECORDS_PATH = ROOT / 'RE_output' / 'content' / 'task_watch_records.bin'

IMAGE_BASE = 0x140000000            # preferred image base of the PE
KNOWN_BASE = 0x7FF641BF0000         # runtime base, stable per reboot session
HEAD_RVA = 0x14241f630 - IMAGE_BASE  # DAT_14241f630 -> base + 0x241f630
STUB_RVA = 0x14036add0 - IMAGE_BASE  # FUN_14036add0 -> base + 0x36add0

RECORD_BYTES = 0x200                # dump window per task record
MAX_TASKS = 64                      # walk cap per latch (per task spec)
POLL_S = 0.005                      # 5 ms polls
PER_PID_S = 300                     # per-pid latch window (matches prior watcher)
DEADLINE_S = 2700                   # 45 min global deadline
IDLE_BREAK_S = 10.0                 # close a pid window after 10 s of null head post-capture

# Pinned next-pointer offset inside a task record: FUN_14036add0 @ RVA 0x36add0
# is "48 8B 01 C3" (mov rax,[rcx]; ret) in the decrypted image -> link at +0x00.
# Confirmed live by the 0x20-stride 2,199-record chain captured 2026-08-15.
NEXT_OFF = 0x00


def ts():
    return time.strftime('%H:%M:%S')


def plausible(p):
    return p is not None and 0x10000000000 < p < 0x7FFFFFFFFFFF


def r64(handle, a):
    try:
        d = read_memory(handle, a, 8)
    except Exception:
        return None
    return struct.unpack('<Q', d)[0] if d and len(d) == 8 else None


def decode_next_off(stub):
    """Cross-check the 4-byte accessor stub of FUN_14036add0 (informational).

    The decrypted image (RE_output/destiny2_unpacked.exe, RVA 0x36add0) holds
    48 8B 01 C3 = mov rax,[rcx]; ret -> link at +0x00.  The LIVE page is
    usually still VMProtect-packed, so this usually fails; NEXT_OFF is pinned
    from the decrypted bytes regardless.  The result is logged per pid.
    Returns (off, desc) or (None, reason).
    """
    if len(stub) < 5:
        return None, 'short read (%d bytes)' % len(stub)
    b = stub[:5]
    if b == b'\x48\x8b\x01\xc3':
        return 0, 'mov rax,[rcx]; ret (next @ +0x00)'
    if b[0] == 0x48 and b[1] == 0x8B and b[2] == 0x41 and b[4] == 0xC3:
        return b[3], 'mov rax,[rcx+0x%02X]; ret (next @ +0x%02X)' % (b[3], b[3])
    if b[0] == 0x8B and b[1] == 0x41 and b[3] == 0xC3:
        return None, '32-bit mov eax,[rcx+0x%02X]; ret - would truncate 64-bit links' % b[2]
    return None, 'unrecognized stub pattern (live page likely still packed)'


def walk_and_capture(handle, base, head, next_off, seen):
    """Walk the task list from head, dump raw records.

    Returns (new_addrs, walked, hops, reason). `hops` = number of plausible
    links followed (0 means the pinned link offset produced no chain).
    New records (not in `seen`) get one frame each: {u64 addr}{u16 len}{bytes}.
    Frames are written by the caller as a single append (one open/append/close
    per capture burst).
    """
    new_addrs = []
    walked = 0
    hops = 0
    frames = bytearray()
    cur = head
    for _ in range(MAX_TASKS):
        if not plausible(cur):
            break
        walked += 1
        try:
            buf = read_memory(handle, cur, RECORD_BYTES)
        except Exception as e:
            # torn/unmapped record: try to follow the link anyway
            nxt = r64(handle, cur + next_off)
            print('  [%s] record @0x%X read FAILED (%s); following link only'
                  % (ts(), cur, e), flush=True)
            if not plausible(nxt):
                return new_addrs, walked, hops, 'link read failed after bad record'
            hops += 1
            cur = nxt
            continue
        if len(buf) < RECORD_BYTES:
            print('  [%s] record @0x%X short read (%d/0x%X)'
                  % (ts(), cur, len(buf), RECORD_BYTES), flush=True)
        nxt = struct.unpack_from('<Q', buf, next_off)[0] if next_off + 8 <= len(buf) else None
        if cur not in seen:
            seen.add(cur)
            new_addrs.append(cur)
            frames += struct.pack('<QH', cur, len(buf)) + buf
        if not plausible(nxt):
            break
        hops += 1
        cur = nxt
    if frames:
        with open(RECORDS_PATH, 'ab') as f:
            f.write(bytes(frames))
    return new_addrs, walked, hops, 'end of list (null/implausible link)'


def latch_pid(pid):
    print('[%s] NEW GAME PID %d' % (ts(), pid), flush=True)
    try:
        handle = open_process(pid)
    except Exception as e:
        print('[%s] open_process(%d) failed: %s' % (ts(), pid, e), flush=True)
        return 0
    try:
        try:
            mb = find_module_base(pid, 'destiny2.exe') or 0
        except Exception:
            mb = 0
        if mb and mb != KNOWN_BASE:
            print('[%s] WARNING module base 0x%X != KNOWN_BASE 0x%X '
                  '(head reads use KNOWN_BASE per session pin)'
                  % (ts(), mb, KNOWN_BASE), flush=True)
        base = KNOWN_BASE

        try:
            stub = read_memory(handle, base + STUB_RVA, 8)
        except Exception as e:
            stub = b''
            print('[%s] stub read FAILED: %s' % (ts(), e), flush=True)
        _off, desc = decode_next_off(stub)
        print('[%s] stub FUN_14036add0 @0x%X: %s -> %s (using pinned NEXT_OFF +0x%02X)'
              % (ts(), base + STUB_RVA, stub.hex() or '(no bytes)', desc, NEXT_OFF), flush=True)

        seen = set()
        captured_any = False
        idle_since = None
        stuck_polls = 0
        t_deadline = time.time() + PER_PID_S
        while time.time() < t_deadline:
            head = r64(handle, base + HEAD_RVA)
            if not plausible(head):
                if captured_any:
                    if idle_since is None:
                        idle_since = time.time()
                    elif time.time() - idle_since > IDLE_BREAK_S:
                        print('[%s] pid %d: head null %.0fs after capture; closing window'
                              % (ts(), pid, IDLE_BREAK_S), flush=True)
                        break
                time.sleep(POLL_S)
                continue
            idle_since = None
            new_addrs, walked, hops, reason = walk_and_capture(handle, base, head, NEXT_OFF, seen)
            if new_addrs:
                captured_any = True
                stuck_polls = 0
                shown = ', '.join('0x%X' % a for a in new_addrs[:6])
                more = ' ... +%d more' % (len(new_addrs) - 6) if len(new_addrs) > 6 else ''
                print('[%s] CAPTURE pid %d: burst of %d new record(s) (walked %d, %s); '
                      'total seen=%d {%s%s}'
                      % (ts(), pid, len(new_addrs), walked, reason, len(seen), shown, more),
                      flush=True)
            elif hops == 0:
                # plausible head but the pinned link offset produced no chain
                stuck_polls += 1
                if stuck_polls == 200:  # ~1 s of 5 ms polls
                    print('[%s] pid %d: head plausible but NO chain with pinned NEXT_OFF +0x%02X '
                          '(structure may differ from the 2026-08-15 build)'
                          % (ts(), pid, NEXT_OFF), flush=True)
                elif stuck_polls == 4000:  # ~20 s
                    print('[%s] pid %d: still no chain; giving up this pid'
                          % (ts(), pid), flush=True)
                    break
            time.sleep(POLL_S)
        print('[%s] pid %d: window closed, %d distinct records captured'
              % (ts(), pid, len(seen)), flush=True)
        return len(seen)
    finally:
        try:
            kernel32.CloseHandle(handle)
        except Exception:
            pass


def main():
    RECORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    print('[%s] task watcher armed (head DAT_14241f630 @ base+0x%X, %d B/record, '
          'walk cap %d, poll %.0f ms, deadline %d min)'
          % (ts(), HEAD_RVA, RECORD_BYTES, MAX_TASKS, POLL_S * 1000, DEADLINE_S // 60),
          flush=True)
    print('[%s] base=0x%X  records->%s' % (ts(), KNOWN_BASE, RECORDS_PATH), flush=True)
    cur_pid = find_pid('destiny2.exe')
    print('[%s] current pid: %s' % (ts(), cur_pid or 'none'), flush=True)
    seen_pids = {cur_pid} if cur_pid else set()

    deadline = time.time() + DEADLINE_S
    total_records = 0
    while time.time() < deadline:
        try:
            cur = find_pid('destiny2.exe')
        except Exception as e:
            print('[%s] find_pid error: %s' % (ts(), e), flush=True)
            cur = None
        if cur and cur not in seen_pids:
            seen_pids.add(cur)
            total_records += latch_pid(cur)
        time.sleep(0.1)

    print('[%s] watcher deadline reached (%d min); total distinct records captured: %d'
          % (ts(), DEADLINE_S // 60, total_records), flush=True)


if __name__ == '__main__':
    main()
