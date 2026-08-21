import ctypes, ctypes.wintypes as wt, sys
sys.path.insert(0, r'C:\Users\rasla\Downloads\destiny-preservation\RE_scripts')
from dump_sunrise_memory import find_pid, open_process

pid = find_pid('destiny2.exe')
if not pid:
    print('no game')
    sys.exit(1)
out = sys.argv[1] if len(sys.argv) > 1 else r'RE_output\content\game_full.dmp'

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
dbghelp = ctypes.WinDLL(r'C:\Users\rasla\Downloads\destiny-preservation\dcv build\dbghelp.dll', use_last_error=True)

MiniDumpWithFullMemory = 0x00000002
MiniDumpWithFullMemoryInfo = 0x00000800
MiniDumpWithHandleData = 0x00000004
MiniDumpWithThreadInfo = 0x00001000
MiniDumpWithUnloadedModules = 0x00000020
MiniDumpWithIndirectlyReferencedMemory = 0x00000040
flags = (MiniDumpWithFullMemory | MiniDumpWithFullMemoryInfo | MiniDumpWithHandleData |
         MiniDumpWithThreadInfo | MiniDumpWithUnloadedModules | MiniDumpWithIndirectlyReferencedMemory)

h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
if not h:
    raise OSError(ctypes.get_last_error(), 'OpenProcess failed')

f = kernel32.CreateFileW(out, 0x40000000, 0, None, 2, 0x80, None)
if f == -1:
    raise OSError(ctypes.get_last_error(), 'CreateFile failed')

ok = dbghelp.MiniDumpWriteDump(h, pid, f, flags, None, None, None)
if not ok:
    err = ctypes.get_last_error()
    print('MiniDumpWriteDump FAILED:', err)
else:
    import os
    print('dumped ->', out, os.path.getsize(out), 'bytes')
kernel32.CloseHandle(f)
kernel32.CloseHandle(h)
