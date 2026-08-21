import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import java.io.FileWriter;
import java.util.LinkedHashSet;

public class RegistrationWriters extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration3.txt");
        LinkedHashSet<Function> done = new LinkedHashSet<Function>();
        out.write("=== writers/references of DAT_14267aa50 (the registration result global) ===\n");
        Address g = toAddr(0x14267aa50L);
        ReferenceIterator rit = currentProgram.getReferenceManager().getReferencesTo(g);
        while (rit.hasNext()) {
            Reference r = rit.next();
            Function f = getFunctionContaining(r.getFromAddress());
            String fn = f != null ? f.getName() : "(none)";
            out.write("ref from 0x" + r.getFromAddress() + " in " + fn + "\n");
            println("ref from 0x" + r.getFromAddress() + " in " + fn);
            if (f != null && !done.contains(f)) {
                done.add(f);
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                out.write("---- " + fn + " ----\n" + c + "\n");
            }
        }
        out.write("=== scan for the -87 constant (0xffffffa9) ===\n");
        Memory mem = currentProgram.getMemory();
        byte[] pat = new byte[]{(byte)0xa9, (byte)0xff, (byte)0xff, (byte)0xff};
        Address cur = mem.getMinAddress();
        int n = 0;
        while (cur != null && n < 30) {
            Address hit = mem.findBytes(cur, pat, null, true, monitor);
            if (hit == null) break;
            Function f = getFunctionContaining(hit);
            String fn = f != null ? f.getName() : "(no function)";
            out.write("0x" + hit + " in " + fn + "\n");
            println("const hit 0x" + hit + " in " + fn);
            if (f != null && !done.contains(f)) {
                done.add(f);
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail)";
                out.write("---- " + fn + " ----\n" + c + "\n");
            }
            n++;
            cur = hit.add(1);
        }
        out.write("=== remaining internals ===\n");
        long[] funcs = {0x1404c9ff0L, 0x1404c9fc0L, 0x1404ca0d0L, 0x140375ad0L, 0x140359a20L, 0x140339f30L, 0x14041dba0L, 0x14174f830L};
        for (long t : funcs) {
            Function f = getFunctionAt(toAddr(t));
            if (f == null || done.contains(f)) continue;
            done.add(f);
            DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
            String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
            out.write("=== " + f.getName() + " (0x" + Long.toHexString(t) + ") ===\n" + c + "\n");
            println("decompiled " + f.getName());
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
