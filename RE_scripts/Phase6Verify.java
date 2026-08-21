// Phase 6: close the mechanical open items.
// Outputs RE_output/export/phase6/{decompiles.txt, func_xrefs.txt, tables.txt}
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

public class Phase6Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase6";

    private static final String[] DECOMPILE = {
        // type->class assignment (last column of master table)
        "0x140e74f80",
        // primitive reader table targets (29, from phase5 tables.txt)
        "0x1409f3330", "0x1409f3970", "0x1409f3a90", "0x1409f3bb0", "0x1409f3cd0",
        "0x1409f3d60", "0x1409f3ed0", "0x1409f3ee0", "0x1409f3f10", "0x1409f4290",
        "0x1409f49f0", "0x1409f4a60", "0x1409f5840", "0x1409f5a00", "0x1409f8d50",
        "0x1409f8f50", "0x1409f9670", "0x1409f9700", "0x1409f9b00", "0x1409f9b30",
        "0x1409f9c80", "0x1409f9e20", "0x1409f9f90", "0x1409f9ff0", "0x1409fa080",
        "0x1409fa0b0", "0x1409fb9e0", "0x1409fc3b0", "0x140b94700",
        // deadorbit trigger context + override writer context
        "0x140325e40",
        // signon bcrypt-property region probe
        "0x144a50fe0",
    };

    private static final String[][] FUNCTION_XREFS = {
        {"0x140364bc0", "FUN_140364bc0 retry loop (find trigger caller)"},
        {"0x140325e40", "FUN_140325e40 endpoint override (find writers)"},
        {"0x140e74f80", "FUN_140e74f80 type->class assignment"},
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpXrefs(new File(dir, "func_xrefs.txt"));
        dumpTables(new File(dir, "tables.txt"));
        dumpDecompiles(new File(dir, "decompiles.txt"));
        println("PHASE6-DONE");
    }

    private void dumpXrefs(File f) throws Exception {
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            for (String[] a : FUNCTION_XREFS) {
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
            // A[128..315] dispatch array tail
            Address a = currentProgram.getAddressFactory().getAddress("0x141FCF6A0");
            w.write("=== dispatch array A[128..315] ===\n");
            for (int i = 128; i < 316; i++) {
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
            // 37 records full 12 qwords
            Address r = currentProgram.getAddressFactory().getAddress("0x141C3CB88");
            w.write("=== 37 response records (0x60 stride, 12 qwords each) ===\n");
            for (int k = 0; k < 37; k++) {
                w.write(String.format("record[%d] @ 0x%X:%n", k, r.getOffset() + k * 0x60L));
                for (int q = 0; q < 12; q++) {
                    long v;
                    try {
                        v = mem.getLong(r.add(k * 0x60 + q * 8));
                    } catch (Exception e) {
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
                    w.write(String.format("    [%2d] 0x%016X  -> 0x%016X%s%n", q, v, vv, extra));
                }
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
                if (n % 8 == 0) {
                    println("decompiled " + n + "/" + DECOMPILE.length);
                }
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
