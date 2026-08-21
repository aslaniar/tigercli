import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import java.io.FileWriter;

public class RegistrationSubtasks extends GhidraScript {
    public void run() throws Exception {
        DecompInterface ifc = new DecompInterface();
        ifc.openProgram(currentProgram);
        FileWriter out = new FileWriter("C:/Users/rasla/Downloads/destiny-preservation/RE_output/export/phase_registration7.txt");
        long[] funcs = {0x14033fed0L, 0x14033ff30L, 0x14033ff70L, 0x1404c9ff0L, 0x1404c9fc0L, 0x1404ca180L, 0x1404ca0d0L, 0x14033deb0L, 0x14033de40L, 0x14032db10L};
        for (long t : funcs) {
            Function f = getFunctionAt(toAddr(t));
            out.write("=== 0x" + Long.toHexString(t) + " " + (f != null ? f.getName() : "(none)") + " ===\n");
            if (f != null) {
                DecompileResults dr = ifc.decompileFunction(f, 60, monitor);
                String c = dr.getDecompiledFunction() != null ? dr.getDecompiledFunction().getC() : "(fail: " + dr.getErrorMessage() + ")";
                out.write(c + "\n");
                println(Long.toHexString(t) + " -> " + f.getName() + " (" + c.split("\n").length + " lines)");
            }
        }
        out.close();
        ifc.dispose();
        println("done");
    }
}
