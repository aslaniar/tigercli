use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

use anyhow::Context;
use tiger_pkg::{DestinyVersion, GameVersion, PackageManager, TagHash};

fn main() -> anyhow::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() < 2 {
        eprintln!("usage: tigercli.exe <packages_dir> <tag_hex> [<tag_hex> ...] [--out <dir>]");
        std::process::exit(2);
    }
    let packages_dir = &args[0];
    let mut out_dir = PathBuf::from(".");
    let mut tags: Vec<String> = Vec::new();
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--out" {
            i += 1;
            if i < args.len() {
                out_dir = PathBuf::from(&args[i]);
            }
        } else {
            tags.push(args[i].clone());
        }
        i += 1;
    }

    let pm = PackageManager::new(
        packages_dir,
        GameVersion::Destiny(DestinyVersion::Destiny2Shadowkeep),
        None,
    )
    .context("PackageManager::new")?;

    std::fs::create_dir_all(&out_dir)?;

    for t in &tags {
        let v = u32::from_str_radix(t, 16).with_context(|| format!("bad tag hex {t}"))?;
        let tag = TagHash(v);
        match pm.get_entry(tag) {
            None => {
                eprintln!("0x{v:08X}: no entry");
                continue;
            }
            Some(e) => {
                println!(
                    "0x{v:08X}: pkg {:04x}/{} size 0x{:x} reference 0x{:08X} type {} subtype {}",
                    tag.pkg_id(),
                    tag.entry_index(),
                    e.file_size,
                    e.reference,
                    e.file_type,
                    e.file_subtype
                );
            }
        }
        match pm.read_tag(tag) {
            Ok(data) => {
                println!("0x{v:08X}: decoded {} B", data.len());
                let head = data.len().min(64);
                println!("0x{v:08X}: head {}", hex::encode(&data[..head]));
                let out_path = out_dir.join(format!("{t}.bin"));
                let mut f = File::create(&out_path)
                    .with_context(|| format!("create {}", out_path.display()))?;
                f.write_all(&data)?;
                println!("0x{v:08X}: wrote {}", out_path.display());
            }
            Err(e) => {
                eprintln!("0x{v:08X}: decode FAILED: {e:#}");
            }
        }
    }
    Ok(())
}
