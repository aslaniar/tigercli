// Query the 16 verified Sunrise anchors + 3 extra hooks in d2_arrivals.
// @category Sunrise
// @author opcode
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.util.task.ConsoleTaskMonitor;

public class GhidraQueryAnchors extends GhidraScript {

    private static final String[][] ANCHORS = {
        {"transport_kind", "0x140405F80"},
        {"http_execute_request", "0x14039AC90"},
        {"signon_readiness_failure", "0x140405450"},
        {"signon_readiness_ready", "0x1404053A0"},
        {"content_config_fetch", "0x1404C9E00"},
        {"content_config_tick", "0x140D4C550"},
        {"content_manifest_gate", "0x1404CA36A"},
        {"bubble_authority_decoder", "0x1403C9FC0"},
        {"content_untracked_getter", "0x1402FACA0"},
        {"content_id_token_load", "0x14005FD6F"},
        {"queuez_object_resolver", "0x140E002D0"},
        {"queuez_family5_subscribe", "0x140BE9370"},
        {"get_item_stat_value", "0x140524720"},
        {"light_value_to_scalar", "0x14054CC10"},
        {"retail_log_enqueue", "0x14035D860"},
        {"retail_log_set_category_verbosity", "0x14035DC80"},
    };

    private static final String[][] EXTRA = {
        {"extra_hook_1", "0x14039B710"},
        {"extra_hook_2", "0x140474660"},
        {"extra_hook_3", "0x140474610"},
    };

    private DecompInterface decomp;
    private ConsoleTaskMonitor monitor;

    @Override
    public void run() throws Exception {
        decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        monitor = new ConsoleTaskMonitor();
        for (String[] a : ANCHORS) {
            query(a[0], a[1]);
        }
        for (String[] a : EXTRA) {
            query(a[0], a[1]);
        }
    }

    private void query(String name, String hex) {
        Address addr = currentProgram.getAddressFactory().getAddress(hex);
        Function func = getFunctionContaining(addr);
        boolean created = false;
        if (func == null) {
            try {
                func = createFunction(addr, name);
                created = true;
            } catch (Exception e) {
                println("QUERY " + name + " @ " + hex + " CREATE-FAIL " + e.getMessage());
                return;
            }
        }
        println("=== " + name + " @ " + hex + " func=" + func.getName()
                + (created ? " (created)" : ""));
        Reference[] refs = getReferencesTo(addr);
        println("  xrefs=" + refs.length);
        for (int i = 0; i < Math.min(15, refs.length); i++) {
            Reference r = refs[i];
            Address from = r.getFromAddress();
            Function rf = getFunctionContaining(from);
            println("    from " + from + " ref=" + r.getReferenceType()
                    + (rf != null ? " func=" + rf.getName() : ""));
        }
        if (refs.length > 15) {
            println("    ... " + (refs.length - 15) + " more");
        }
        try {
            DecompileResults res = decomp.decompileFunction(func, 30, monitor);
            if (res != null && res.decompileCompleted()) {
                println("  DECOMPILED:");
                String c = res.getDecompiledFunction().getC();
                for (String line : c.split("\n")) {
                    println("    " + line);
                }
            } else {
                println("  decompile status: "
                        + (res != null ? res.getErrorMessage() : "null"));
            }
        } catch (Exception e) {
            println("  decompile error: " + e.getMessage());
        }
        println("");
    }
}
