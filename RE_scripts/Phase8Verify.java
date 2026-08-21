// Phase 8: activity-state command handlers + registration blob closure.
// Outputs RE_output/export/phase8/{decompiles.txt, func_xrefs.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase8Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase8";

    // the 18 distinct activity-state command handlers from FUN_140b47e70
    // (0x140b94700 = shared 3B stub, registered for 6 and 8)
    private static final String[] DECOMPILE = {
        "0x140b46940", // cmd 0
        "0x140b46580", // cmd 1
        "0x140b456c0", // cmd 2 = slice-set transition (KNOWN; re-decompile for the file)
        "0x1448e3b08", // cmd 3 (thunk)
        "0x140b45070", // cmd 7
        "0x140b46a10", // cmd 9
        "0x140b46a30", // cmd 10
        "0x140b46be0", // cmd 0xb
        "0x146f3dd4d", // cmd 0xc (thunk)
        "0x144274e86", // cmd 0xd (thunk)
        "0x140b469b0", // cmd 0xe
        "0x140b46a60", // cmd 0xf
        "0x140b46500", // cmd 0x10
        "0x140b464c0", // cmd 4
        "0x140b46d90", // cmd 5
        "0x140b46dd0", // cmd 0x12
        "0x140b46460", // cmd 0x14
        // registration blob closure: family sweep + family-0 register functions.
        // Force-create functions at the blob starts (scan back for prologues done
        // offline; these are the containing-function entries).
        "0x140be9600", // family sweep region start (approx; create+decompile)
        "0x140be6200", // family-0 register region start (approx)
        // completion callbacks (2nd arg consumers) for command semantics
        "0x140b467b0", "0x140b46790", "0x140b46660", "0x140b46690",
        "0x140b46630", "0x140b46620", "0x140b46610", "0x140b46800",
        "0x140b46820", "0x140b46860", "0x140b46850", "0x140b467a0",
        "0x140b467e0", "0x140b46840", "0x140b46780", "0x140b46760",
        "0x140b46870", "0x140b468c0", "0x140b46750",
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpDecompiles(new File(dir, "decompiles.txt"));
        println("PHASE8-DONE");
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
                if (fn == null) {
                    // try force-creating at this address (for the blob regions)
                    try {
                        fn = createFunction(addr, "CMD_" + hex.substring(2));
                        if (fn != null) {
                            println("created function at " + hex);
                        }
                    } catch (Exception ignored) {
                    }
                }
                w.write("===== " + hex + " (" + (fn != null ? fn.getName() : "NO FUNC") + ")\n");
                if (fn == null) {
                    continue;
                }
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
                n++;
                if (n % 8 == 0) {
                    println("decompiled " + n + "/" + DECOMPILE.length);
                }
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
