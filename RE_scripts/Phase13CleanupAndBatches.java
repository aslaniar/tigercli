// Phase 13: (a) purge the 4,001 noise sweep-functions from the cold runs;
// (b) decompile the schema-stream builders; (c) cold-run batch A+B (top named).
// Outputs RE_output/export/phase13/{decompiles.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase13CleanupAndBatches extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase13";

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();

        // (a) purge noise: remove functions whose body is inside the two runs AND
        // whose name matches the Phase10 auto-created pattern (FUN_145d/fun_1489 etc).
        // Keep any function >= 0x14896A000-range middle band (those are real).
        long removed = 0;
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        java.util.List<Function> toRemove = new java.util.ArrayList<>();
        while (it.hasNext()) {
            Function f = it.next();
            long ep = f.getEntryPoint().getOffset();
            boolean inRun1 = ep >= 0x145D0D000L && ep < 0x14609C000L;
            boolean inRun2 = ep >= 0x14896A000L && ep < 0x148A5E000L;
            if ((inRun1 || inRun2) && f.getName().startsWith("FUN_")) {
                toRemove.add(f);
            }
        }
        for (Function f : toRemove) {
            removeFunction(f);
            removed++;
        }
        println("purged noise functions: " + removed);

        // (b)+(c) decompiles
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        String[] targets = {
            // schema-stream builders (schema-namejoin REQUEST fallback)
            "0x140351340", "0x140351730",
            // cold-run batch A: top named (from coldrun-naming.md)
            "0x1484dfccc", "0x148014486", "0x14876b719", "0x1461d4dca",
            "0x145224ef9", "0x14784d3aa", "0x1453e6eee",
            // middle-band head slice (mutation-vs-data texture, first 8 of 60)
            "0x14609d803", "0x14609d8c3", "0x14609d943", "0x14609d9c3",
            "0x14609da43", "0x14609db03", "0x14609db83", "0x14609dc03",
        };
        try (BufferedWriter w = new BufferedWriter(
                new FileWriter(new File(dir, "decompiles.txt")))) {
            for (String hex : targets) {
                Address addr = currentProgram.getAddressFactory().getAddress(hex);
                Function fn = getFunctionContaining(addr);
                if (fn == null) {
                    try {
                        fn = createFunction(addr, "P13_" + hex.substring(2));
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
            }
        }
        println("PHASE13-DONE");
    }
}
