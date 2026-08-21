// Phase 4: wave-3 requery — xrefs, table dumps, decompile batch.
// Outputs RE_output/export/phase4/{string_xrefs.txt, func_xrefs.txt, tables.txt, decompiles.txt}
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

public class Phase4Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase4";

    private static final String[][] STRING_ANCHORS = {
        {"0x141C22810", "spawn gate refusal text (re-run)"},
        {"0x141BE9940", "activity-message name table (re-run)"},
    };

    private static final String[][] FUNCTION_XREFS = {
        {"0x140b46660", "FUN_140b46660 slice-set log formatter (find caller)"},
        {"0x1416f1900", "FUN_1416f1900 push dispatcher"},
        {"0x1416f1800", "FUN_1416f1800 push-event decoder"},
        {"0x1416f1490", "FUN_1416f1490 response dispatcher"},
        {"0x140e04e30", "FUN_140e04e30 queue-event apply"},
        {"0x140e10c10", "FUN_140e10c10 push apply"},
        {"0x140e0a0b0", "FUN_140e0a0b0 per-family parser"},
        {"0x1403503e0", "FUN_1403503e0 schema-table builder"},
        {"0x14038f7f0", "FUN_14038f7f0 upload driver"},
        {"0x14174d2a0", "FUN_14174d2a0 AES-GCM codec"},
        {"0x1404b9200", "FUN_1404b9200 tagReflection decoder A"},
        {"0x1404bf920", "FUN_1404bf920 tagReflection decoder B"},
        {"0x141746990", "FUN_141746990 ring->middleware forwarder"},
        {"0x140dfdbc0", "FUN_140dfdbc0 validator"},
    };

    // (label, addr, qwords)
    private static final String[][] TABLE_DUMPS = {
        {"crypto vtable DAT_1426be2e8", "0x1426BE2E8", "24"},
        {"schema table DAT_142439c70 sample", "0x142439C70", "64"},
        {"dispatch .data slot array 0x141FCF6A0", "0x141FCF6A0", "128"},
        {"descriptor[0] 0x141C3C600 (18 qwords)", "0x141C3C600", "18"},
        {"descriptor[1] 0x141C3C690", "0x141C3C690", "18"},
        {"descriptor[2] 0x141C3C720", "0x141C3C720", "18"},
        {"descriptor[3] 0x141C3C7B0", "0x141C3C7B0", "18"},
        {"descriptor[4] 0x141C3C840", "0x141C3C840", "18"},
        {"descriptor[5] 0x141C3C8D0", "0x141C3C8D0", "18"},
        {"descriptor[6] 0x141C3C960", "0x141C3C960", "18"},
        {"descriptor[7] 0x141C3C9F0", "0x141C3C9F0", "18"},
        {"family-4 push table DAT_141fbcb60", "0x141FBCB60", "15"},
        {"failure string table DAT_1420488e0", "0x1420488E0", "40"},
    };

    private static final String[] DECOMPILE = {
        // push dispatcher chain
        "0x1416f1900", "0x1416f1800", "0x140e10c10", "0x140e04e30",
        // per-family parser
        "0x140e0a0b0",
        // tagReflection decoders
        "0x1404b9200", "0x1404bf920",
        // AES-GCM codec
        "0x14174d2a0", "0x14174d0e0",
        // schema-table builder
        "0x1403503e0",
        // per-kind family-4 applies
        "0x140e078f0", "0x140e07ba0", "0x140e08000", "0x140e080b0",
        "0x140e08200", "0x140e08140", "0x140e083a0",
        // response dispatcher + validator
        "0x1416f1490", "0x140dfdbc0",
        // deadorbit pump
        "0x14038ead0", "0x14039baa0",
        // GCM thunk (runtime addr -> image VA)
        "0x1405224ef9",
        // ring->middleware forwarder
        "0x141746990",
        // spawn gate / slice-set context
        "0x140b46660",
        // upload driver context
        "0x14038f7f0",
        // subscription-request encoder region (from wave-1 claim)
        "0x140e0e4e0",
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpStringXrefs(new File(dir, "string_xrefs.txt"));
        dumpFunctionXrefs(new File(dir, "func_xrefs.txt"));
        dumpTables(new File(dir, "tables.txt"));
        dumpDecompiles(new File(dir, "decompiles.txt"));
        println("PHASE4-DONE");
    }

    private void dumpStringXrefs(File f) throws Exception {
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            for (String[] a : STRING_ANCHORS) {
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
        println("string xrefs done");
    }

    private void dumpFunctionXrefs(File f) throws Exception {
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
        println("func xrefs done");
    }

    private void dumpTables(File f) throws Exception {
        Memory mem = currentProgram.getMemory();
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            for (String[] t : TABLE_DUMPS) {
                Address a = currentProgram.getAddressFactory().getAddress(t[1]);
                int n = Integer.parseInt(t[2]);
                w.write("=== " + t[0] + " @ " + t[1] + " (" + n + " qwords) ===\n");
                for (int i = 0; i < n; i++) {
                    long v;
                    try {
                        v = mem.getLong(a.add(i * 8));
                    } catch (Exception e) {
                        w.write(String.format("  [%3d] <unreadable>\n", i));
                        continue;
                    }
                    long vv = v;
                    if (v >= 0x7FF000000000L && v < 0x800000000000L) {
                        vv = v - 0x7FF6300A0000L + 0x140000000L; // runtime->image
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
                if (n % 8 == 0) {
                    println("decompiled " + n + "/" + DECOMPILE.length);
                }
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
