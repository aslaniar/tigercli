// Phase 7: verify GLM-lane claims + close the six open items.
// Outputs RE_output/export/phase7/{decompiles.txt, tables.txt, func_xrefs.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase7Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase7";

    private static final String[] DECOMPILE = {
        // opcode-comparison home (opcode-sweep prime suspect)
        "0x140dfec50",
        // family-3 registration blobs (function containing each)
        "0x140be9765", "0x140be6245",
        // roster notify trio
        "0x140faad40", "0x140faaf30", "0x140fab000",
        // roster notify-hub singleton accessor
        "0x140fca3f0",
    };

    private static final String[][] TABLE_DUMPS = {
        {"type->decoder registry DAT_14280E3E0 (308 qwords)", "0x14280E3E0", "308"},
        {"notify hub DAT_141FCDEC8", "0x141FCDEC8", "16"},
        {"handler obj type100 0x141FBF2F8", "0x141FBF2F8", "12"},
        {"handler obj type102 0x141FBF300", "0x141FBF300", "12"},
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpXrefs(new File(dir, "func_xrefs.txt"));
        dumpTables(new File(dir, "tables.txt"));
        dumpDecompiles(new File(dir, "decompiles.txt"));
        // grep decompiles output for opcode immediates and write hits
        println("PHASE7-DONE");
    }

    private void dumpXrefs(File f) throws Exception {
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            String[][] targets = {
                {"0x141fbf2f8", "handler obj type 100 (s->ws req)"},
                {"0x141fbf300", "handler obj type 102 (s->ws rsp)"},
                {"0x141fcdec8", "roster notify hub DAT_141FCDEC8"},
                {"0x140faad40", "roster fresh notify FUN_140faad40"},
            };
            for (String[] a : targets) {
                Address addr = currentProgram.getAddressFactory().getAddress(a[0]);
                Reference[] refs = getReferencesTo(addr);
                w.write("=== " + a[1] + " @ " + a[0] + " xrefs=" + refs.length + "\n");
                for (Reference r : refs) {
                    Address from = r.getFromAddress();
                    Function fn = getFunctionContaining(from);
                    w.write("    from " + from + " ref=" + r.getReferenceType()
                            + (fn != null ? " func=" + fn.getName() : "") + "\n");
                }
            }
        }
        println("xrefs done");
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
                    DecompileResults res = decomp.decompileFunction(fn, 120, mon);
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
                println("decompiled " + n + "/" + DECOMPILE.length);
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
