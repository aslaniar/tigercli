import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.io.FileWriter;

public class RegistrationFinal extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration5.txt");
        long[] funcs = {0x14689840bL, 0x14033df20L, 0x14033dee0L, 0x140381960L, 0x14035a2c0L, 0x14035d170L};
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
                println(Long.toHexString(t) + " -> none");
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
