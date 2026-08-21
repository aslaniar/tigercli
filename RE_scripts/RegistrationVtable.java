import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class RegistrationVtable extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration6.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        Memory mem = currentProgram.getMemory();
        byte[] pat = new byte[]{(byte)0xdd, (byte)0x81, (byte)0x03, (byte)0x14, 0, 0, 0, 0};
        Address cur = mem.getMinAddress();
        int n = 0;
        out.write("=== pointer-to-validator scan (the vtable slots) ===\n");
        while (cur != null && n < 20) {
            Address hit = mem.findBytes(cur, pat, null, true, monitor);
            if (hit == null) break;
            out.write("ptr at 0x" + hit + "\n");
            println("ptr at 0x" + hit);
            ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(hit);
            while (rit.hasNext()) {
                Reference r = rit.next();
                Function f = getFunctionContaining(r.getFromAddress());
                String fn = f != null ? f.getName() : "(none)";
                out.write("  ref from 0x" + r.getFromAddress() + " in " + fn + "\n");
                if (f != null && !done.contains(f)) {
                    done.add(f);
                    DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                    String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                    out.write("---- " + fn + " ----\n" + c + "\n");
                    println("  decompiled ref-owner " + fn);
                }
            }
            n++;
            cur = hit.add(8);
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
