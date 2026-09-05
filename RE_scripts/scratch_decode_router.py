#!/usr/bin/env python3
import struct, sys
sys.path.insert(0, "/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_scripts")
from pe_reader import PE
pe = PE("/Users/rubenaslanian/Documents/opencode/sunrise-fork/RE_output/destiny2_unpacked_full.exe")

BASE = 0x140000000
BYTE_TBL = 0x1416E71E0
OFF_TBL  = 0x1416E7134

byte_tbl = pe.read(BYTE_TBL, 0x5d)
print("byte table (family-1 -> case index) at 0x1416E71E0, 93 entries:")
case_of_family = {}
for i, b in enumerate(byte_tbl):
    fam = i + 1
    case_of_family[fam] = b
    print(f"  family=0x{fam:02x} ({fam:3d})  case_index={b}")

maxcase = max(byte_tbl)
n = maxcase + 1
print(f"\nmax case index = {maxcase} -> offset table has {n} dwords at 0x1416E7134")
off_tbl = pe.read(OFF_TBL, n * 4)
offsets = [struct.unpack_from("<I", off_tbl, j * 4)[0] for j in range(n)]
print("offset table (case index -> RVA, base 0x140000000):")
targets = {}
for j, off in enumerate(offsets):
    tgt = BASE + off
    print(f"  case=0x{j:02x} ({j:2d})  rva=0x{off:08x}  target=0x{tgt:X}")
    targets[j] = tgt

print("\n--- FULL RESOLVED ARM TABLE: family value -> target address ---")
for fam in sorted(case_of_family):
    b = case_of_family[fam]
    print(f"  family 0x{fam:02x} ({fam:3d})  ->  0x{targets[b]:X}")
