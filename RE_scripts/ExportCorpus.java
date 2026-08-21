// Phase 1 export: strings dump, function census, decompile batch.
// Writes RE_output/export/{strings_dump.txt, functions.csv, decompiled_archive.txt}
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.DataIterator;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class ExportCorpus extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export";

    private static final String[] DECOMPILE_TARGETS = {
        // transport_kind callers
        "0x141742200", "0x14174c7c0", "0x141742540",
        // http_execute_request caller
        "0x14039b440",
        // signon readiness caller
        "0x141073380",
        // content_untracked_getter callers
        "0x140327110", "0x14038dfc0", "0x1403cc8c0", "0x1403ccb40", "0x1403cccc0",
        // queuez resolver callers
        "0x140e013d0", "0x140e01520",
        // extra_hook_3 caller
        "0x141074740",
        // config pipeline helpers
        "0x1404ca210", "0x1404c9820", "0x1404ca890",
        "0x14039b2f0", "0x14039b300", "0x14039b040", "0x14039b060",
        "0x1403248a0", "0x140391f00", "0x140391a70", "0x1402f8700",
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();

        dumpFunctions(dir);
        dumpStrings(dir);
        dumpDecompilations(dir);

        println("EXPORT-DONE dir=" + OUT_DIR);
    }

    private void dumpFunctions(File dir) throws IOException {
        File f = new File(dir, "functions.csv");
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            long count = 0;
            while (it.hasNext() && !monitor.isCancelled()) {
                Function fn = it.next();
                w.write(fn.getEntryPoint() + "," + fn.getBody().getNumAddresses() + ","
                        + fn.getName() + "\n");
                count++;
            }
            println("FUNCTIONS count=" + count);
        }
    }

    private void dumpStrings(File dir) throws IOException {
        File f = new File(dir, "strings_dump.txt");
        long count = 0;
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            DataIterator it = currentProgram.getListing().getDefinedData(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Data d = it.next();
                Object val = d.getValue();
                if (val instanceof String) {
                    String s = (String) val;
                    if (s.length() >= 6) {
                        w.write(d.getAddress() + "\t" + s.replaceAll("[\\r\\n]", " ") + "\n");
                        count++;
                    }
                }
            }
        }
        println("STRINGS count=" + count);
    }

    private void dumpDecompilations(File dir) throws IOException {
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        File f = new File(dir, "decompiled_archive.txt");
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f, true))) {
            for (String hex : DECOMPILE_TARGETS) {
                Address addr = currentProgram.getAddressFactory().getAddress(hex);
                Function fn = getFunctionContaining(addr);
                w.write("===== " + hex);
                w.write(fn != null ? " (" + fn.getName() + ")" : " (no function)");
                w.write("\n");
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
            }
        }
        println("DECOMPILE batch done");
    }
}
