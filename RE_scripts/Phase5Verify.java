// Phase 5: final requery — last decompiles + mechanical registry dumps.
// Outputs RE_output/export/phase5/{decompiles.txt, tables.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase5Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase5";

    private static final String[] DECOMPILE = {
        // entity: push case arms + injection point + queue encoder
        "0x140e0f000", "0x140b47e70", "0x1416f4aa0",
        // signon: GCM dispatch + ring flush
        "0x145224ef9", "0x14174d130",
        // family4: inventory row helpers + per-family apply + queue-event apply
        "0x140dfacf0", "0x140dfb730", "0x140dfa7d0", "0x140dfb210",
        "0x140e01960", "0x140e02740", "0x140e07510",
        // sub-blob copiers
        "0x140e07d30", "0x140e071f0", "0x140e07af0", "0x140e07e60",
        "0x140e07dd0", "0x140e07f30", "0x140e08670",
        // deadorbit: retry loop + enqueue/pop + state mapper
        "0x140364bc0", "0x14039aad0", "0x14039aba0", "0x14039b130",
        // bap: thunk bodies to settle table base/index semantics
        "0x14106f860", "0x14106f870",
    };

    // (label, addr, qwords)
    private static final String[][] TABLE_DUMPS = {
        {"37 per-type records 0x141C3CB88 (0x60 stride)", "0x141C3CB88", "37"},
        {"family-4 push objects 0x141FBCC00", "0x141FBCC00", "64"},
        {"primitive readers A DAT_141F94F38", "0x141F94F38", "32"},
        {"primitive readers B DAT_141F94DC0", "0x141F94DC0", "32"},
        {"message-type registry DAT_142808A70", "0x142808A70", "64"},
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpTables(new File(dir, "tables.txt"));
        dumpDecompiles(new File(dir, "decompiles.txt"));
        println("PHASE5-DONE");
    }

    private void dumpTables(File f) throws Exception {
        Memory mem = currentProgram.getMemory();
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            for (String[] t : TABLE_DUMPS) {
                Address a = currentProgram.getAddressFactory().getAddress(t[1]);
                int n = Integer.parseInt(t[2]);
                w.write("=== " + t[0] + " @ " + t[1] + " ===\n");
                for (int i = 0; i < n; i++) {
                    long v;
                    try {
                        v = mem.getLong(a.add(i * 8));
                    } catch (Exception e) {
                        w.write(String.format("  [%3d] <unreadable>%n", i));
                        continue;
                    }
                    long vv = v;
                    if (v >= 0x7FF000000000L && v < 0x800000000000L) {
                        vv = v - 0x7FF6300A0000L + 0x140000000L;
                    }
                    String extra = "";
                    if (vv >= 0x140000000L && vv < 0x149000000L) {
                        try {
                            Address ta = currentProgram.getAddressFactory()
                                    .getAddress(Long.toHexString(vv));
                            byte[] b = new byte[48];
                            mem.getBytes(ta, b);
                            StringBuilder s = new StringBuilder();
                            for (byte x : b) {
                                if (x == 0) break;
                                if (x >= 32 && x < 127) s.append((char) x);
                                else { s.append("."); break; }
                            }
                            if (s.length() > 2) extra = "  \"" + s + "\"";
                        } catch (Exception ignored) {
                        }
                    }
                    w.write(String.format("  [%3d] 0x%016X  -> 0x%016X%s%n", i, v, vv, extra));
                }
                w.write("\n");
            }
        }
        println("tables done");
    }

    private void dumpDecompiles(File f) throws Exception {
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            int n = 0;
            for (String hex : DECOMPILE) {
                Address addr = currentProgram.getAddressFactory().getAddress(hex);
                Function fn = getFunctionContaining(addr);
                w.write("===== " + hex + " (" + (fn != null ? fn.getName() : "NO FUNC") + ")\n");
                if (fn == null) {
                    continue;
                }
                try {
                    DecompileResults res = decomp.decompileFunction(fn, 60, mon);
                    if (res != null && res.decompileCompleted()) {
                        w.write(res.getDecompiledFunction().getC());
                        w.write("\n");
                    } else {
                        w.write("STATUS: " + (res != null ? res.getErrorMessage() : "null") + "\n");
                    }
                } catch (Exception e) {
                    w.write("ERROR: " + e.getMessage() + "\n");
                }
                n++;
                if (n % 6 == 0) {
                    println("decompiled " + n + "/" + DECOMPILE.length);
                }
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
