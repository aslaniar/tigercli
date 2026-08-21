import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class VtableOwner2 extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_vtable_owner2.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        long[] targets = {0x1435ef598L, 0x1435ef584L, 0x141dc84d8L};
        for (long t : targets) {
            out.write("=== xrefs to 0x" + Long.toHexString(t) + " ===\n");
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(toAddr(t));
            int n = 0;
            while (rit.hasNext() && n < 20) {
                Reference r = rit.next();
                Function f = getFunctionContaining(r.getFromAddress());
                String fn = f != null ? f.getName() : "(none)";
                out.write("  from 0x" + r.getFromAddress() + " in " + fn + "\n");
                if (f != null && !done.contains(f)) {
                    done.add(f);
                    DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                    String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                    out.write("---- " + fn + " ----\n" + c + "\n");
                    println("decompiled " + fn);
                }
                n++;
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
