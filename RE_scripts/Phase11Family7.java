// Phase 11: family-7 closeout decompiles + xrefs (agent REQUEST execution).
// Outputs RE_output/export/phase11/{decompiles.txt, func_xrefs.txt, string_xrefs.txt}
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

public class Phase11Family7 extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase11";

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();

        // xrefs: registration callers + strings
        try (BufferedWriter w = new BufferedWriter(new FileWriter(new File(dir, "func_xrefs.txt")))) {
            String[][] targets = {
                {"0x140be49d0", "FUN_140be49d0 family-7 register (find callers)"},
                {"0x140e08f00", "FUN_140e08f00 family register (all callers)"},
            };
            for (String[] a : targets) {
                Address addr = currentProgram.getAddressFactory().getAddress(a[0]);
                Reference[] refs = getReferencesTo(addr);
                w.write("=== " + a[1] + " @ " + a[0] + " xrefs=" + refs.length + "\n");
                for (Reference r : refs) {
                    w.write("    from " + r.getFromAddress() + " ref=" + r.getReferenceType() + "\n");
                }
            }
            String[][] anchors = {
                {"0x141beb4f8", "string 'investment character'"},
                {"0x141beb510", "string 'investment account'"},
            };
            for (String[] a : anchors) {
                Address addr = currentProgram.getAddressFactory().getAddress(a[0]);
                Reference[] refs = getReferencesTo(addr);
                w.write("=== " + a[1] + " @ " + a[0] + " xrefs=" + refs.length + "\n");
                for (Reference r : refs) {
                    Function fn = getFunctionContaining(r.getFromAddress());
                    w.write("    from " + r.getFromAddress() + " func="
                            + (fn != null ? fn.getName() : "?") + "\n");
                }
            }
        }

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();

        // decompiles incl. force-creation at the two blob regions + the method cluster
        String[] targets = {
            "0x140be9765", // blob A (family sweep)
            "0x140be6245", // blob B (family-0 register)
            "0x140e09ac0", // family validation (1511B)
            "0x140304050", // family-name resolver
            "0x140be4f80", "0x140be4fd0", "0x140be4060", "0x140be4120",
            "0x140be41c0", "0x140be4290", // family-7 state-object method candidates
        };
        try (BufferedWriter w = new BufferedWriter(new FileWriter(new File(dir, "decompiles.txt")))) {
            for (String hex : targets) {
                Address addr = currentProgram.getAddressFactory().getAddress(hex);
                Function fn = getFunctionContaining(addr);
                if (fn == null) {
                    try {
                        fn = createFunction(addr, "F7_" + hex.substring(2));
                        if (fn != null) {
                            println("created " + hex);
                        }
                    } catch (Exception ignored) {
                    }
                }
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
            }
        }
        println("PHASE11-DONE");
    }
}
