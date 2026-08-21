// Phase 3: verify claims (xrefs) + targeted decompile batch.
// Outputs RE_output/export/phase3/{string_xrefs.txt, func_xrefs.txt, ptr_dump.txt, decompiles.txt}
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
import java.io.IOException;

public class Phase3Verify extends GhidraScript {

    private static final String OUT_DIR =
            "C:\\Users\\rasla\\Downloads\\destiny-preservation\\RE_output\\export\\phase3";

    // Claimed string anchors to xref (addr, label)
    private static final String[][] STRING_ANCHORS = {
        // bap-dispatch
        {"0x141CA2948", "bap failed_to_find_message_recipient"},
        {"0x141CA30D8", "bap BAP ID %2d desc:%s"},
        {"0x141CA3580", "bap b->c shello req (first desc)"},
        {"0x141CA2888", "bap unknown_message_type"},
        {"0x141CA2A00", "bap response fatal"},
        {"0x141CA2AB0", "bap push fatal"},
        {"0x141C259B0", "bap handle response"},
        {"0x141C25A40", "bap handle_response_internal"},
        {"0x141C26DC8", "bap c_investment_bap_message_push_handler::handle_message"},
        {"0x141C26D90", "bap investment push handler scratch"},
        // signon
        {"0x141CA34E0", "signon %d.%d.%d.%d:%d formatter"},
        {"0x141CA3528", "signon primary_bap_server_ip_address"},
        {"0x141CA3548", "signon primary_bap_server_port"},
        {"0x141BF4678", "signon SignOn?platform=%s&build=%s"},
        {"0x141BE2440", "signon _sending_signon_request"},
        {"0x141CA3990", "signon b->c ssc req"},
        // entity
        {"0x141C9F870", "entity simulation_queue_bap_message_queue_event_apply"},
        {"0x141C9F920", "entity simulation_queue_bap_push_event_apply"},
        {"0x141C22810", "entity spawn gate refusal text"},
        {"0x141CA10C0", "entity replication property schema"},
        {"0x141BE9940", "entity activity-message name table"},
        {"0x141C14360", "entity slice-set transition"},
        {"0x141C14328", "entity payload spawn identifier unavailable"},
        // deadorbit
        {"0x141BD0740", "deadorbit multipart builder"},
        {"0x141BD06E8", "deadorbit %s://%s:%d%s"},
        {"0x141F16C15", "deadorbit config host (.data)"},
        {"0x141F16C98", "deadorbit config port (.data)"},
        {"0x141F16CB8", "deadorbit config token (.data)"},
        {"0x141F84E70", "deadorbit second config instance"},
        // family4
        {"0x141C3C208", "family4 client_to_bap_subscription_request"},
        {"0x141C25BA8", "family4 queuez-binary-diff"},
        {"0x141C25BC0", "family4 queuez-oodle-data"},
    };

    // Functions whose callers we want (addr, label)
    private static final String[][] FUNCTION_XREFS = {
        {"0x1417459A0", "FUN_1417459a0 connection-failure reporter"},
        {"0x140E08F00", "FUN_140e08f00 family subscribe register"},
        {"0x142439C70", "DAT_142439c70 family-4 schema table"},
        {"0x14039B440", "FUN_14039b440 DW HTTP executor"},
        {"0x14039AC90", "http_execute_request thunk"},
        {"0x140E05C10", "FUN_140e05c10 store getter (family5 path)"},
        {"0x141F16E6D", "deadorbit 0x1000 spool region"},
        {"0x141F85058", "DW HTTP thread state"},
        {"0x1403CCCC0", "FUN_1403cccc0 lease bitmap consumer"},
    };

    // Decompile batch (deduped, all five agents' top requests)
    private static final String[] DECOMPILE = {
        // bap dispatch candidates
        "0x14173E050", "0x1417480E0", "0x14174B250", "0x141749BE0", "0x1417417D0",
        "0x141744E00", "0x14173BFC0", "0x14174B9C0", "0x141746520", "0x141741DE0",
        "0x14174C000",
        // bap connection steps
        "0x14173FED0", "0x14173F1C0", "0x14173F4D0", "0x14173F7B0", "0x141740610",
        "0x141740990", "0x1417407B0", "0x14173B750", "0x1417459A0",
        // signon
        "0x141073630", "0x141070BF0", "0x141071620",
        "0x1404076D0", "0x140407580", "0x140407660", "0x140407730", "0x1404077C0",
        "0x140407900", "0x140407CC0",
        "0x14046A6C0", "0x14046AA00", "0x14046A4A0", "0x14046AED0", "0x14046AF70",
        "0x14046AFD0", "0x14046A500", "0x14046A750", "0x14046B170", "0x14046A0C0",
        "0x14046B1F0",
        // family4
        "0x140E010C0", "0x140E00080", "0x140E00350", "0x140E008A0", "0x140E05DA0",
        "0x140E05EB0", "0x140DFD740", "0x1404C74D0", "0x1404C74B0", "0x14034C190",
        "0x140351070", "0x1403512E0", "0x14034C290", "0x14034EB90", "0x140351D90",
        "0x140E08FA0", "0x140E05C10", "0x140BE9430", "0x140BE54A0", "0x140BDE860",
        "0x140BDB930", "0x140E06380",
        // entity
        "0x1404CCD90", "0x1403CCB80", "0x1404CD230", "0x1403CC1E0", "0x1403CD110",
        "0x1404C96F0", "0x1404C9950", "0x140343010",
        // deadorbit
        "0x14038D140", "0x14038E400", "0x14038F7F0", "0x1403191F0", "0x14039ABA0",
        "0x14038CD70", "0x14038E350",
    };

    @Override
    public void run() throws Exception {
        File dir = new File(OUT_DIR);
        dir.mkdirs();
        dumpStringXrefs(new File(dir, "string_xrefs.txt"));
        dumpFunctionXrefs(new File(dir, "func_xrefs.txt"));
        dumpPointerTable(new File(dir, "ptr_dump.txt"));
        dumpDecompiles(new File(dir, "decompiles.txt"));
        println("PHASE3-DONE");
    }

    private void dumpStringXrefs(File f) throws IOException {
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
        println("xrefs done");
    }

    private void dumpFunctionXrefs(File f) throws IOException {
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

    private void dumpPointerTable(File f) throws Exception {
        Memory mem = currentProgram.getMemory();
        Address start = currentProgram.getAddressFactory().getAddress("0x141CA3500");
        Address end = currentProgram.getAddressFactory().getAddress("0x141CA3A00");
        try (BufferedWriter w = new BufferedWriter(new FileWriter(f))) {
            for (Address a = start; a.compareTo(end) < 0; a = a.add(8)) {
                long v = mem.getLong(a);
                w.write(a + " -> 0x" + Long.toHexString(v));
                if (v >= 0x140000000L && v < 0x149000000L) {
                    try {
                        Address t = currentProgram.getAddressFactory()
                                .getAddress(Long.toHexString(v));
                        byte[] b = new byte[32];
                        mem.getBytes(t, b);
                        StringBuilder s = new StringBuilder();
                        for (byte x : b) {
                            if (x == 0) break;
                            if (x >= 32 && x < 127) s.append((char) x);
                            else { s.append("."); }
                        }
                        w.write("  \"" + s + "\"");
                    } catch (Exception ignored) {
                    }
                }
                w.write("\n");
            }
        }
        println("ptr dump done");
    }

    private void dumpDecompiles(File f) throws IOException {
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
                    DecompileResults res = decomp.decompileFunction(fn, 45, mon);
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
                if (n % 10 == 0) {
                    println("decompiled " + n + "/" + DECOMPILE.length);
                }
            }
        }
        println("decompiles done: " + DECOMPILE.length);
    }
}
