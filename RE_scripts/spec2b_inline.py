import ctypes, json, sys, time
sys.path.insert(0, "RE_scripts")
import dump_sunrise_memory as dsm
IMG = 0x140000000
OUT = sys.argv[1] if len(sys.argv) > 1 else "RE_output/content/registry_logout_post.json"
pid = dsm.find_pid("destiny2.exe"); assert pid, "FATAL: destiny2.exe not running"
h = dsm.open_process(pid); base = dsm.find_module_base(pid, "destiny2.exe")
addr = base + (0x14280E3E0 - IMG)
raw = dsm.read_memory(h, addr, 308 * 8)
time.sleep(1)
assert raw == dsm.read_memory(h, addr, 308 * 8), "registry changed between reads"
raw10 = int.from_bytes(raw[10*8:11*8], "little")
sb = raw10 - 0x141FBF1C0 + IMG if raw10 else 0
img = lambda r: r - sb + IMG if sb and r > 0x7FF000000000 else r
reg = {}
for t in range(308):
    v = int.from_bytes(raw[t*8:t*8+8], "little")
    if v: reg.setdefault(hex(img(v)), []).append(t)
json.dump({"decoder_registry": reg, "sunrise_base": sb}, open(OUT, "w"))
types = sorted(t for v in reg.values() for t in v)
print(OUT, "populated=%d" % len(types), "types=%s" % types)
