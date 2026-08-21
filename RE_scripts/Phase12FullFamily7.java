// Phase 12: family-7 closeout against the FULL image (d2_full) — the cold runs
// were never analyzed when the original xrefs ran. Re-hunt the consumer code.
// Outputs RE_output/export/phase12/{func_xrefs.txt, decompiles.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase12FullFamily7 extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase12";

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();

        // 1. xrefs on d2_full: family-7 strings + register + the descriptor table
        try (BufferedWriter w = new BufferedWriter(new FileWriter(new File(dir, "func_xrefs.txt")))) {
            String[][] targets = {
                {"0x141beb4f8", "string 'investment character'"},
                {"0x141beb510", "string 'investment account'"},
                {"0x140be49d0", "FUN_140be49d0 family-7 register"},
                {"0x141f92fc8", "DAT_141F92FC8 family-5 descriptor (family-7 sibling zone)"},
                {"0x140e08f00", "FUN_140e08f00 register (all callers incl cold runs)"},
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

        // 2. decompile every NEW caller found in the cold runs (bounded: 24 functions)
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        try (BufferedWriter w = new BufferedWriter(new FileWriter(new File(dir, "decompiles.txt")))) {
            java.util.List<String> found = new java.util.ArrayList<>();
            for (String[] a : new String[][]{{"0x140be49d0"}, {"0x140e08f00"}, {"0x141f92fc8"}}) {
                Address addr = currentProgram.getAddressFactory().getAddress(a[0]);
                for (Reference r : getReferencesTo(addr)) {
                    Function fn = getFunctionContaining(r.getFromAddress());
                    if (fn == null) {
                        continue;
                    }
                    String ep = fn.getEntryPoint().toString();
                    if (!found.contains(ep) && found.size() < 24) {
                        found.add(ep);
                    }
                }
            }
            for (String ep : found) {
                Function fn = currentProgram.getFunctionManager()
                        .getFunctionContaining(currentProgram.getAddressFactory().getAddress(ep));
                if (fn == null) {
                    continue;
                }
                w.write("===== " + ep + " (" + fn.getName() + ")\n");
                try {
                    DecompileResults res = decomp.decompileFunction(fn, 90, mon);
                    if (res != null && res.decompileCompleted()) {
                        w.write(res.getDecompiledFunction().getC());
                        w.write("\n");
                    } else {
                        w.write("STATUS: " + (res != null ? res.getErrorMessage() : "null") + "\n");
                    }
                } catch (Exception e) {
                    w.write("ERROR: " + e.getMessage() + "\n");
                }
            }
            println("decompiled " + found.size() + " caller functions");
        }
        println("PHASE12-DONE");
    }
}
