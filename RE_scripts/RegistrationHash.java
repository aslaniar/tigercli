import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class RegistrationHash extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration4.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        Function validator = getFunctionAt(toAddr(0x140381dd0L));
        out.write("=== callers of the validator FUN_140381dd0 ===\n");
        ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(validator.getEntryPoint());
        while (rit.hasNext()) {
            Reference r = rit.next();
            Function f = getFunctionContaining(r.getFromAddress());
            if (f != null && !done.contains(f)) {
                done.add(f);
                out.write("--- caller " + f.getName() + " (0x" + Long.toHexString(f.getEntryPoint().getOffset()) + ") from 0x" + r.getFromAddress() + " ---\n");
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
                out.write(c + "\n");
                println("caller: " + f.getName() + " (" + c.split("\n").length + " lines)");
            }
        }
        Function thunk = getFunctionAt(toAddr(0x14480a10fL));
        out.write("=== the hash thunk @ 0x14480a10f ===\n");
        if (thunk != null) {
            done.add(thunk);
            DecompileResults dr = ifc.decompileFunction(thunk, 60, monitor);
            String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
            out.write(c + "\n");
            println("thunk decompiled: " + c.split("\n").length + " lines");
        } else {
            out.write("(no function at the thunk address)\n");
            println("no function at the thunk");
        }
        out.write("=== callers of FUN_140381930 (the result writer) ===\n");
        Function writer = getFunctionAt(toAddr(0x140381930L));
        rit = currentProgram.getReferenceManager().getReferencesTo(writer.getEntryPoint());
        while (rit.hasNext()) {
            Reference r = rit.next();
            Function f = getFunctionContaining(r.getFromAddress());
            if (f != null && !done.contains(f)) {
                done.add(f);
                out.write("--- writer-caller " + f.getName() + " (0x" + Long.toHexString(f.getEntryPoint().getOffset()) + ") ---\n");
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                out.write(c + "\n");
                println("writer-caller: " + f.getName());
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
