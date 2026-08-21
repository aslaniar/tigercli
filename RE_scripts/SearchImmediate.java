import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.util.task.TaskMonitor;

public class SearchImmediate extends GhidraScript {
    public void run() throws Exception {
        int[] targets = {0x80807850, 0x8131931D, 0x8080784E, 0x8080784A, 0x80807860, 0x80807861};
        Memory mem = currentProgram.getMemory();
        Listing listing = currentProgram.getListing();
        ReferenceManager rm = currentProgram.getReferenceManager();
        for (int t : targets) {
            byte[] pat = new byte[] {(byte)(t & 0xFF), (byte)((t >> 8) & 0xFF), (byte)((t >> 16) & 0xFF), (byte)((t >> 24) & 0xFF)};
            println("=== scan for 0x" + Integer.toHexString(t) + " (LE bytes " + String.format("%02x %02x %02x %02x", pat[0], pat[1], pat[2], pat[3]) + ") ===");
            int n = 0;
            Address cur = mem.getMinAddress();
            while (cur != null && n < 60) {
                Address hit = mem.findBytes(cur, pat, null, true, monitor);
                if (hit == null) break;
                Function f = getFunctionContaining(hit);
                Instruction ins = listing.getInstructionAt(hit);
                String fn = f != null ? f.getName() : "(no function)";
                String kind = ins != null ? "instr" : "data ";
                ReferenceIterator xit = rm.getReferencesTo(hit);
                int xc = 0; while (xit.hasNext()) { xit.next(); xc++; }
                println(String.format("0x%08x %s in %s (0x%s)%s", hit.getOffset(), kind, fn, f != null ? Long.toHexString(f.getEntryPoint().getOffset()) : "-", xc > 0 ? " xrefs=" + xc : ""));
                n++;
                cur = hit.add(1);
            }
            println("hits: " + n);
        }
    }
}
