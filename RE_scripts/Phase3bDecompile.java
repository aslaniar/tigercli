// Phase 3.5: decompile the xref-discovered dispatch-adjacent functions.
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.util.task.ConsoleTaskMonitor;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;

public class Phase3bDecompile extends GhidraScript {

    private static final String OUT =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase3\\decompiles3b.txt";

    private static final String[] TARGETS = {
        "0x141746ba0", // BAP ID %2d desc:%s name mapper
        "0x141743160", // desc table consumer
        "0x1416f0f60", // simulation_queue_bap_message_queue_event_apply
        "0x1416f17a0", // simulation_queue_bap_push_event_apply
        "0x140e0e4e0", // c_investment_bap_message_push_handler::handle_message
        "0x140e01c30", // handle response
        "0x140e02280", // handle_response_internal
        "0x1417454a0", // primary_bap_server_ip/port reader
        "0x141740c20", // relay formatter user
        "0x14038d080", // deadorbit multipart POST builder
        "0x1403918d0", // deadorbit URL assembler
        "0x140b46660", // slice-set transition
        "0x140be49d0", // family-4 subscribe register caller
        "0x141748e80", // connection reconfigure helper
        "0x141746460", // connection teardown helper
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT).getParentFile();
        dir.mkdirs();
        DecompInterface decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        try (BufferedWriter w = new BufferedWriter(new FileWriter(OUT))) {
            for (String hex : TARGETS) {
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
            }
        }
        println("PHASE3B-DONE");
    }
}
