// First-look at the newly captured cold-run code: create functions + decompile a
// sample across both runs. Outputs RE_output/export/phase10/decompiles.txt
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.SourceType;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase10ColdRuns extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase10";

    private static final long[][] RUNS = {
        {0x145D0D000L, 0x14609C000L},
        {0x14896A000L, 0x148A5E000L},
    };

    @Override
    public void run() throws Exception {
        File dir = new File("C:\\Users\\rasla\\Downloads\\destiny-preservation"
                + "\\RE_output\\export\\phase10");
        dir.mkdirs();

        // 1. disassemble + create functions across both runs
        int created = 0;
        for (long[] run : RUNS) {
            Address start = currentProgram.getAddressFactory().getAddress(Long.toHexString(run[0]));
            Address end = currentProgram.getAddressFactory().getAddress(Long.toHexString(run[1]));
            Address cur = start;
            while (cur.compareTo(end) < 0) {
                disassemble(cur);
                cur = cur.add(64);
            }
        }
        for (long[] run : RUNS) {
            Address a = currentProgram.getAddressFactory().getAddress(Long.toHexString(run[0]));
            Address b = currentProgram.getAddressFactory().getAddress(Long.toHexString(run[1]));
            Address cur = a;
            while (cur.compareTo(b) < 0) {
                if (getInstructionAt(cur) != null && getFunctionContaining(cur) == null) {
                    Function f = createFunction(cur, null);
                    if (f != null) {
                        created++;
                    }
                }
                cur = cur.add(1);
                if (created > 4000) {
                    break;
                }
            }
        }
        println("functions created in cold runs: " + created);

        // 2. count + decompile a sample
        int total = 0;
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(
                currentProgram.getAddressFactory().getAddress("145d0d000"), true);
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        try (BufferedWriter w = new BufferedWriter(
                new FileWriter(new File(dir, "decompiles.txt")))) {
            while (it.hasNext()) {
                Function f = it.next();
                if (f.getEntryPoint().getOffset() > 0x148A5E000L) {
                    break;
                }
                total++;
                if (total <= 40) {
                    try {
                        DecompileResults res = decomp.decompileFunction(f, 60, mon);
                        if (res != null && res.decompileCompleted()) {
                            w.write("===== " + f.getEntryPoint() + " (" + f.getName() + ", "
                                    + f.getBody().getNumAddresses() + "B)\n");
                            w.write(res.getDecompiledFunction().getC());
                            w.write("\n");
                        }
                    } catch (Exception ignored) {
                    }
                }
            }
        }
        println("functions in cold-run range: " + total + " (first 40 decompiled)");
        println("PHASE10-DONE");
    }
}
