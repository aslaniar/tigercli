import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class VtableOwner extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_vtable_owner.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        long[] slots = {0x141dc84e4L, 0x141dc84f8L, 0x141dc84dcL, 0x141dc8500L};
        for (long s : slots) {
            out.write("=== xrefs to the vtable slot region 0x" + Long.toHexString(s) + " ===\n");
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(toAddr(s));
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function f = getFunctionContaining(r.getFromAddress());
                String fn = f != null ? f.getName() : "(none)";
                out.write("  from 0x" + r.getFromAddress() + " in " + fn + "\n");
                if (f != null && !done.contains(f)) {
                    done.add(f);
                    DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                    String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
                    out.write("---- " + fn + " ----\n" + c + "\n");
                    println("decompiled " + fn + " (" + c.split("\n").length + " lines)");
                }
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
