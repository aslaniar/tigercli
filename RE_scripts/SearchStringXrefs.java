import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;

public class SearchStringXrefs extends GhidraScript {
    public void run() throws Exception {
        long[] targets = {0x141c1f2e8L, 0x141c1f320L, 0x141c1f792L, 0x141c3de78L};
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration.txt");
        for (long t : targets) {
            Address a = toAddr(t);
            println("=== string @ 0x" + Long.toHexString(t) + " ===");
            out.write("=== string @ 0x" + Long.toHexString(t) + " ===\n");
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(a);
            int n = 0;
            while (rit.hasNext() && n < 12) {
                Reference r = rit.next();
                Address from = r.getFromAddress();
                Function f = getFunctionContaining(from);
                String fn = f != null ? f.getName() : "(none)";
                println(String.format("  xref from 0x%s in %s (entry 0x%s)", from, fn,
                    f != null ? Long.toHexString(f.getEntryPoint().getOffset()) : "-"));
                out.write(String.format("  xref from 0x%s in %s (entry 0x%s)\n", from, fn,
                    f != null ? Long.toHexString(f.getEntryPoint().getOffset()) : "-"));
                if (f != null && !f.isThunk()) {
                    DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                    String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(decompile failed: " + dr.getErrorMessage() + ")";
                    println("---- decompile " + fn + " ----");
                    println(c);
                    out.write("---- decompile " + fn + " ----\n" + c + "\n");
                }
                n++;
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
