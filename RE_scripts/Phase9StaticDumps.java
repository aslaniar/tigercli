// Phase 9 (static part): the two .rdata gaps + hash table head + 15 push objects + quantizer decompiles.
// Outputs RE_output/export/phase9/{tables.txt, decompiles.txt}
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

public class Phase9StaticDumps extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase9";

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        Memory mem = currentProgram.getMemory();
        try (BufferedWriter w = new BufferedWriter(
                new FileWriter(new File(dir, "tables.txt")))) {
            for (String[] t : new String[][]{
                    {"gap A (183B) 0x141CA0618-0x141CA06D3", "0x141CA0618", "183"},
                    {"gap B (0x1C2B) 0x141CA1208-0x141CA13CA", "0x141CA1208", "450"},
                    {"hash table head 0x141FBCD08", "0x141FBCD08", "128"},
                    {"15 push objects 0x141C26E28 (0x30 stride x 15)", "0x141C26E28", "90"},
            }) {
                Address a = currentProgram.getAddressFactory().getAddress(t[1]);
                int n = Integer.parseInt(t[2]);
                w.write("=== " + t[0] + " ===\n");
                byte[] b = new byte[n];
                try {
                    mem.getBytes(a, b);
                } catch (Exception e) {
                    w.write("<unreadable>\n\n");
                    continue;
                }
                for (int i = 0; i < n; i += 16) {
                    StringBuilder hex = new StringBuilder();
                    StringBuilder asc = new StringBuilder();
                    for (int j = 0; j < 16 && i + j < n; j++) {
                        hex.append(String.format("%02X ", b[i + j]));
                        asc.append(b[i + j] >= 32 && b[i + j] < 127 ? (char) b[i + j] : '.');
                    }
                    long va = a.getOffset() + i;
                    w.write(String.format("0x%X  %-48s %s%n", va, hex, asc));
                }
                w.write("\n");
            }
        }
        println("tables done");

        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        try (BufferedWriter w = new BufferedWriter(
                new FileWriter(new File(dir, "decompiles.txt")))) {
            for (String hex : new String[]{
                    "0x140351340", "0x140351730", "0x1403516d0", "0x1404c16c0",
            }) {
                Address addr = currentProgram.getAddressFactory().getAddress(hex);
                Function fn = getFunctionContaining(addr);
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
        println("PHASE9-STATIC-DONE");
    }
}
