import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class RegistrationDeepDive extends GhidraScript {
    public void run() throws Exception {
        long[] funcs = {0x140380ab0L, 0x140380dd0L, 0x140a45540L, 0x141071c90L, 0x1404c99e0L, 0x140380c00L};
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration2.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        for (long t : funcs) {
            Function f = getFunctionAt(toAddr(t));
            if (f == null) { println("no function at 0x" + Long.toHexString(t)); continue; }
            done.add(f);
            out.write("=== FUN @ 0x" + Long.toHexString(t) + " (" + f.getName() + ") ===\n");
            DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
            String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
            out.write(c + "\n");
            println("decompiled " + f.getName() + " (" + c.split("\n").length + " lines)");
        }
        Function machine = getFunctionAt(toAddr(0x141074740L));
        out.write("=== CALLERS of the registration state machine ===\n");
        ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(machine.getEntryPoint());
        while (rit.hasNext()) {
            Reference r = rit.next();
            Function caller = getFunctionContaining(r.getFromAddress());
            if (caller != null && !done.contains(caller)) {
                done.add(caller);
                out.write("--- caller " + caller.getName() + " (0x" + Long.toHexString(caller.getEntryPoint().getOffset()) + ") ---\n");
                DecompileResults dr = ifc.decompileFunction(caller, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                out.write(c + "\n");
                println("caller: " + caller.getName());
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
