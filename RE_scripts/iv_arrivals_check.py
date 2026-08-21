# iv_arrivals_check.py -- check the IV value in the d2_arrivals project
# (94% image, a DIFFERENT capture session). If healthy there too, the healthy
# value is a stable file constant; if it differs, it's a boot-time write.
import os

LOG = r"C:\Users\rasla\Downloads\destiny-preservation\RE_output\ghidra\iv_writer_hunt_arrivals.log"
out = None

def log(s):
    global out
    print(s)
    out.write(s + "\n")
    out.flush()

def addr_of(v):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v)

def getb(a, n):
    try:
        from jpype import JArray, JByte
        buf = JArray(JByte)(n)
        got = currentProgram.getMemory().getBytes(addr_of(a), buf)
        return b''.join(bytes([x & 0xFF]) for x in buf)
    except Exception as e:
        log("getb err: %s" % e)
        return None

def hexb(b):
    return " ".join("%02X" % x for x in b) if b else "(unreadable)"

def main():
    global out
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    out = open(LOG, "w", encoding="utf-8")
    log("=== IV CHECK IN d2_arrivals PROJECT ===")
    log("program: %s" % currentProgram.getName())
    log("image base: %s" % hex(currentProgram.getImageBase().getOffset()))
    healthy = bytes.fromhex('d62ab2c10cc01bc535db7b8655c7dc3b')
    failing = bytes.fromhex('d62ab2c1f5dc168d3fdb7b8655c7dc3b')
    for a, n in [(0x141F44CE0, 16), (0x141B7CAC8, 16), (0x141F44C00, 16)]:
        b = getb(a, n)
        log("0x%X: %s" % (a, hexb(b)))
        if b is not None:
            log("  == healthy? %s  == failing? %s" % (b == healthy, b == failing))
    # also list the memory block that holds the IV site
    mem = currentProgram.getMemory()
    try:
        blk = mem.getBlock(addr_of(0x141F44CE0))
        log("block containing IV: %s 0x%X..0x%X init=%s" % (blk.getName(), blk.getStart().getOffset(), blk.getEnd().getOffset(), blk.isInitialized()))
    except Exception as e:
        log("block query err: %s" % e)
    log("=== DONE ===")
    out.close()
    print("DONE")

main()
