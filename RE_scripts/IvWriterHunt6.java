// IvWriterHunt6.java -- disassemble the whole second .text (0x143CC9000..
// 0x148A5F000) at 64-byte stride, then scan EVERY instruction for resolved
// operands into the struct/IV range [0x141F44C00, 0x141F44D20]; report writes.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Listing;
import java.io.BufferedWriter;
import java.io.FileWriter;

public class IvWriterHunt6 extends GhidraScript {
    @Override
    public void run() throws Exception {
        BufferedWriter out = new BufferedWriter(new FileWriter(
            "C:/Users/rasla/Downloads/destiny-preservation/RE_output/ghidra/iv_writer_hunt6.log"));
        out.write("=== IV WRITER HUNT PASS 6 (full second .text disasm + write scan) ===\n");
        out.write("program: " + currentProgram.getName() + "\n");
        println("start");

        long start = 0x143CC9000L;
        long end   = 0x148A5F000L;
        Listing listing = currentProgram.getListing();

        long cur = start;
        int calls = 0;
        while (cur < end) {
            if (listing.getInstructionAt(toAddr(cur)) == null) {
                try {
                    disassemble(toAddr(cur));
                    calls++;
                } catch (Exception e) {
                    // not disassemblable at this seed; keep going
                }
            }
            cur += 64;
        }
        out.write("disassemble calls: " + calls + "\n");
        println("disasm done: " + calls);

        int total = 0;
        int hits = 0;
        Instruction insn = listing.getFirstInstruction(true);
        while (insn != null && !monitor.isCancelled()) {
            total++;
            int n = insn.getNumOperands();
            if (n > 0) {
                for (int oi = 0; oi < n; oi++) {
                    try {
                        Address a = insn.getAddress(oi);
                        if (a != null) {
                            long off = a.getOffset();
                            if (off >= 0x141F44C00L && off <= 0x141F44D20L) {
                                hits++;
                                String fname = "(no func)";
                                if (getFunctionContaining(insn.getAddress()) != null) {
                                    fname = getFunctionContaining(insn.getAddress()).getName();
                                }
                                out.write(String.format("0x%08X op%d -> 0x%X %s | %s | %s%n",
                                    insn.getAddress().getOffset(), oi, off,
                                    insn.getFlowType(), insn.toString(), fname));
                            }
                        }
                    } catch (Exception e) {
                        // ignore un-resolvable operand
                    }
                }
            }
            insn = listing.getInstructionAfter(insn);
        }
        out.write("instructions scanned: " + total + "\n");
        out.write("struct-range hits: " + hits + "\n");
        out.write("=== IV-WRITER-HUNT6 COMPLETE ===\n");
        out.close();
        println("done: " + total + " insn, " + hits + " hits");
    }
}
