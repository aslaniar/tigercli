using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

// Full tag decoder + investment walk: container -> root -> slots (tag+class).
class VendorWalk {
    [System.Runtime.InteropServices.DllImport(@"C:\Users\rasla\Downloads\destiny-preservation\dcv build\bin\x64\oo2core_3_win64.dll")]
    static extern long OodleLZ_Decompress(byte[] src, long n, byte[] dst, long dn, int f, int c, long v, IntPtr p1, long l1, IntPtr p2, IntPtr p3, IntPtr p4, long l2, int tp);

    static byte[] primary, alternate, nonceBase;
    static string pkgDir = @"C:\Users\rasla\Downloads\destiny-preservation\dcv build\packages";
    static Dictionary<uint, (byte[] data, int ec, long et, long bt, string stem)> pkgCache = new();

    static (byte[], int, long, long, string) LoadPkg(uint pid) {
        if (pkgCache.TryGetValue(pid, out var c)) return c;
        string newest = null; int best = -1;
        foreach (var f in Directory.GetFiles(pkgDir, "*.pkg")) {
            var parts = Path.GetFileNameWithoutExtension(f).Split('_');
            if (!uint.TryParse(parts[^2], System.Globalization.NumberStyles.HexNumber, null, out var id) || id != pid) continue;
            int patch = int.Parse(parts[^1]);
            if (patch > best) { best = patch; newest = f; }
        }
        var d = File.ReadAllBytes(newest);
        int ec = BitConverter.ToInt32(d, 0xB4);
        long et = BitConverter.ToUInt32(d, 0x110) + 96;
        var entry = (d, ec, et, et + ec * 16 + 32, string.Join("_", Path.GetFileNameWithoutExtension(newest).Split('_')[..^1]));
        pkgCache[pid] = entry;
        return entry;
    }

    static byte[] DecodeTag(uint tag) {
        uint pid = (tag - 0x80800000u) >> 13;
        uint idx = tag & 0x1FFFu;
        var (data, ec, et, bt, stem) = LoadPkg(pid);
        long bi = BitConverter.ToInt64(data, (int)(et + idx * 16 + 8));
        uint sb = (uint)(bi & 0x3FFF); int so = (int)(((bi >> 14) & 0x3FFF) << 4); int sz = (int)(bi >> 28);
        var nonce = (byte[])nonceBase.Clone();
        nonce[0] ^= (byte)((pid >> 8) & 0xFF); nonce[1] = 0xF9; nonce[11] ^= (byte)(pid & 0xFF);
        var blob = new List<byte>();
        uint b = sb;
        while (blob.Count < so + sz) {
            long rec = bt + b * 48;
            uint off = BitConverter.ToUInt32(data, (int)rec);
            uint bsize = BitConverter.ToUInt32(data, (int)rec + 4);
            ushort bpatch = BitConverter.ToUInt16(data, (int)rec + 8);
            ushort flags = BitConverter.ToUInt16(data, (int)rec + 10);
            var btag = new byte[16]; Array.Copy(data, (int)rec + 32, btag, 0, 16);
            var bdata = File.ReadAllBytes(Path.Combine(pkgDir, stem + "_" + bpatch + ".pkg"));
            var ct = new byte[bsize]; Array.Copy(bdata, (int)off, ct, 0, (int)bsize);
            byte[] block = ct;
            if ((flags & 2) != 0) {
                var pt = new byte[bsize];
                using var g = new AesGcm((flags & 4) != 0 ? alternate : primary, 16);
                g.Decrypt(nonce, ct, btag, pt);
                block = pt;
            }
            if ((flags & 1) != 0) {
                var dst = new byte[0x40000];
                long prod = OodleLZ_Decompress(block, block.Length, dst, dst.Length, 0, 0, 0, IntPtr.Zero, 0, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, 0, 3);
                if (prod <= 0) {
                    prod = OodleLZ_Decompress(block, block.Length, dst, dst.Length, 1, 0, 0, IntPtr.Zero, 0, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, 0, 3);
                    if (prod <= 0) throw new InvalidDataException($"Oodle decompress failed for block {b} (f=0 and f=1 retry) — refusing to append raw bytes");
                }
                block = dst[..(int)prod];
            }
            blob.AddRange(block);
            b++;
        }
        return blob.ToArray()[so..(so + sz)];
    }

    static uint ClassOf(uint tag) {
        var (data, ec, et, bt, stem) = LoadPkg((tag - 0x80800000u) >> 13); // pid
        return BitConverter.ToUInt32(data, (int)(et + (tag & 0x1FFF) * 16));
    }

    static void Main() {
        var kt = File.ReadAllBytes(@"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\key_table.bin");
        alternate = kt[0..16]; var identity = kt[16..32]; nonceBase = kt[32..44];
        var token = Encoding.ASCII.GetBytes("2MFioXto7iAUN4Qj");
        primary = new byte[16];
        for (int i = 0; i < 16; i++) primary[i] = (byte)(token[i] + identity[i]);

        foreach (uint container in new uint[] { 0x8133719C }) {
            try {
                var gb = DecodeTag(container);
                int n = 0;
                var sw = new StringBuilder();
                for (int o = 8; o + 4 <= gb.Length; o += 4) {
                    uint v = BitConverter.ToUInt32(gb, o);
                    if (v >= 0x80800000u && v < 0x82000000u) n++;
                }
                Console.WriteLine($"globals blob 0x{container:X8}: {gb.Length} B, taglike: {n}");
                for (int o = 0; o + 4 <= gb.Length; o += 4) {
                    uint v = BitConverter.ToUInt32(gb, o);
                    if (v < 0x80800000u || v >= 0x82000000u) continue;
                    string cs;
                    try { cs = $"0x{ClassOf(v):X8}"; } catch { cs = "?"; }
                    sw.AppendLine($"+0x{o:X} tag=0x{v:X8} class={cs}");
                }
                File.WriteAllText(@"C:\Users\rasla\Downloads\destiny-preservation\RE_output\content\investment_root_slots.txt", sw.ToString());
                Console.WriteLine(sw.ToString());
            } catch (Exception e) { Console.WriteLine($"0x{container:X8} fail: {e.Message}"); }
        }
        return;
        // ---- legacy single-container path below ----
        uint containerLegacy = 0x80EC3F62;
        var root = DecodeTag(containerLegacy);
        Console.WriteLine($"investment root: {root.Length} B");
        // children at +0x10, 16B records: {tag, 12B}
        for (int s = 0; s < 8; s++) {
            int ro = 0x10 + s * 16;
            if (ro + 4 > root.Length) break;
            uint stag = BitConverter.ToUInt32(root, ro);
            if (stag == 0) continue;
            Console.WriteLine($"child[{s}] tag=0x{stag:X8}");
            try {
                var cb = DecodeTag(stag);
                Console.WriteLine($"  -> {cb.Length} B, head: {Convert.ToHexString(cb, 0, Math.Min(48, cb.Length))}");
                File.WriteAllBytes($@"C:\Users\rasla\AppData\Local\Temp\opencode\inv_child_{s:X}.bin", cb);
                // recurse one level: if this child looks like a slot table (16B recs from +8),
                // decode ITS children too and classify
                int sub = (cb.Length - 8) / 16;
                var sw = new StringBuilder();
                sw.AppendLine($"# child[{s}] 0x{stag:X8} ({cb.Length} B) - subclasses:");
                int shown = 0;
                for (int t = 0; t < sub && shown < 130; t++) {
                    uint st2 = BitConverter.ToUInt32(cb, 8 + t * 16);
                    if (st2 < 0x80800000u || st2 >= 0x82000000u) continue;
                    string cls2;
                    try { cls2 = $"0x{ClassOf(st2):X8}"; } catch { cls2 = "?"; }
                    sw.AppendLine($"  subslot[{t,3}] tag=0x{st2:X8} class={cls2}");
                    shown++;
                }
                File.WriteAllText($@"C:\Users\rasla\AppData\Local\Temp\opencode\inv_child_{s:X}_sub.txt", sw.ToString());
                Console.WriteLine($"  subclasses listed: {shown}");
            } catch (Exception e) { Console.WriteLine("  decode fail: " + e.Message); }
        }
    }
}
