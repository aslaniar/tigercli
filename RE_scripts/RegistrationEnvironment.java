import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.address.Address;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class RegistrationEnvironment extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration9.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        long[] funcs = {0x1453de4c4L, 0x140348260L, 0x140348270L, 0x14039b300L, 0x14039b2f0L, 0x14039a5e0L, 0x140391f00L, 0x140391a70L};
        for (long t : funcs) {
            Function f = getFunctionAt(toAddr(t));
            out.write("=== 0x" + Long.toHexString(t) + " " + (f != null ? f.getName() : "(none)") + " ===\n");
            if (f != null) {
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
                out.write(c + "\n");
                println(Long.toHexString(t) + " -> " + f.getName() + " (" + c.split("\n").length + " lines)");
            } else {
                out.write("(no function)\n");
            }
        }
        out.write("=== scan for calls to the validator (call instruction targets) ===\n");
        Address val = toAddr(0x140381dd0L);
        ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(val);
        while (rit.hasNext()) {
            Reference r = rit.next();
            Function f = getFunctionContaining(r.getFromAddress());
            String fn = f != null ? f.getName() : "(none)";
            out.write("ref from 0x" + r.getFromAddress() + " in " + fn + "\n");
            println("validator ref: 0x" + r.getFromAddress() + " in " + fn);
            if (f != null && !done.contains(f)) {
                done.add(f);
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                out.write("---- " + fn + " ----\n" + c + "\n");
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
