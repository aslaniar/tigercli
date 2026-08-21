import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.FunctionManager;

public class CountRunFunctions extends GhidraScript {
    public void run() throws Exception {
        long[][] ranges = {
            {0x145D0D000L, 0x14609C000L},
            {0x14896A000L, 0x148A5E000L}
        };
        FunctionManager fm = currentProgram.getFunctionManager();
        FunctionIterator it = fm.getFunctions(true);
        int[] counts = new int[ranges.length];
        java.util.List<String> names = new java.util.ArrayList<>();
        while (it.hasNext()) {
            Function f = it.next();
            long a = f.getEntryPoint().getOffset();
            for (int i = 0; i < ranges.length; i++) {
                if (a >= ranges[i][0] && a < ranges[i][1]) {
                    counts[i]++;
                    if (names.size() < 20) names.add(String.format("0x%08x %s", a, f.getName()));
                    break;
                }
            }
        }
        println("run1 (0x145D0D000-0x14609C000) functions: " + counts[0]);
        println("run2 (0x14896A000-0x148A5E000) functions: " + counts[1]);
        println("sample names:");
        for (String n : names) println("  " + n);
        println("TOTAL in captured-run ranges: " + (counts[0] + counts[1]));
    }
}
