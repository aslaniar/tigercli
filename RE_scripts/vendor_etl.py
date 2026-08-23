#!/usr/bin/env python3
"""vendor_etl.py - populate vendors/vendor_sale_items from the Bungie-API manifest extract.

Source : community_forks/season-of-arivals-manifest-master/tables/DestinyVendorDefinition.json
Target : a sqlite DB whose `vendors` / `vendor_sale_items` tables match the REAL
         schema in RE_build/Sunrise-fork-inventory/Sunrise/src/server/persistence/
         persistence.cpp (CREATE TABLE IF NOT EXISTS block).

Usage:
  python3 vendor_etl.py --manifest <DestinyVendorDefinition.json> --db <state.db> [--dry-run]

Behavior:
  * Uses existing tables if present (schema must match); creates them otherwise.
  * Full-replace idempotency: one transaction deletes prior rows from BOTH target
    tables, then inserts every manifest vendor + sale entry. Re-running the same
    source yields identical row counts.
  * --dry-run reports counts without writing.
"""

import argparse
import json
import os
import sqlite3
import sys

DEFAULT_MANIFEST = (
    "/Users/rubenaslanian/Documents/opencode/sunrise-fork/"
    "community_forks/season-of-arivals-manifest-master/tables/"
    "DestinyVendorDefinition.json"
)

SCHEMA_VENDORS = """
CREATE TABLE IF NOT EXISTS vendors (
  vendor_hash   TEXT PRIMARY KEY,
  vendor_index  INTEGER NOT NULL,
  name          TEXT,
  item_list_json TEXT NOT NULL
)
"""

SCHEMA_SALE_ITEMS = """
CREATE TABLE IF NOT EXISTS vendor_sale_items (
  vendor_hash    TEXT NOT NULL REFERENCES vendors(vendor_hash),
  vendor_item_index INTEGER NOT NULL,
  item_hash      TEXT NOT NULL,
  quantity       INTEGER NOT NULL,
  currencies_json TEXT,
  action_json    TEXT,
  category_index INTEGER NOT NULL,
  display_category_index INTEGER NOT NULL,
  minimum_level  INTEGER NOT NULL,
  maximum_level  INTEGER NOT NULL,
  inventory_bucket_hash INTEGER NOT NULL,
  visibility_scope INTEGER NOT NULL,
  purchasable_scope INTEGER NOT NULL,
  socket_overrides_json TEXT,
  PRIMARY KEY (vendor_hash, vendor_item_index)
)
"""


def load_manifest(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise SystemExit("manifest root is not an object: %r" % type(data).__name__)
    return data


def norm_json(value, empty):
    """Normalize a nullable manifest field into stable JSON text."""
    if value is None:
        value = empty
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def build_rows(data):
    """Flatten the manifest into vendor rows + sale-item rows."""
    vendor_rows = []
    item_rows = []
    for vhash, v in data.items():
        dp = v.get("displayProperties") or {}
        name = dp.get("name")
        item_list = v.get("itemList") or []
        vendor_rows.append(
            (
                str(vhash),                       # vendor_hash (key == inner hash, verified)
                int(v["index"]),                  # vendor_index
                name,                             # name
                json.dumps(item_list, separators=(",", ":")),  # item_list_json
            )
        )
        for e in item_list:
            item_rows.append(
                (
                    str(vhash),                          # vendor_hash
                    int(e["vendorItemIndex"]),           # vendor_item_index
                    str(int(e["itemHash"])),             # item_hash (TEXT per schema)
                    int(e["quantity"]),                  # quantity
                    norm_json(e.get("currencies"), []),  # currencies_json
                    norm_json(e.get("action"), {}),      # action_json
                    int(e["categoryIndex"]),             # category_index
                    int(e["displayCategoryIndex"]),      # display_category_index
                    int(e["minimumLevel"]),              # minimum_level
                    int(e["maximumLevel"]),              # maximum_level
                    int(e["inventoryBucketHash"]),       # inventory_bucket_hash
                    int(e["visibilityScope"]),           # visibility_scope
                    int(e["purchasableScope"]),          # purchasable_scope
                    norm_json(e.get("socketOverrides"), []),  # socket_overrides_json
                )
            )
    return vendor_rows, item_rows


def ensure_schema(conn):
    """Create target tables only when absent; never alter an existing schema."""
    conn.execute(SCHEMA_VENDORS)
    conn.execute(SCHEMA_SALE_ITEMS)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--db", required=True, help="sqlite target path (use a COPY)")
    ap.add_argument("--dry-run", action="store_true", help="report counts, write nothing")
    args = ap.parse_args()

    data = load_manifest(args.manifest)
    vendor_rows, item_rows = build_rows(data)

    print("manifest vendors        : %d" % len(data))
    print("vendors with itemList   : %d" % sum(1 for r in vendor_rows if r[3] != "[]"))
    print("sale entries flattened  : %d" % len(item_rows))

    # sanity: no duplicate (vendor_hash, vendor_item_index)
    seen = set()
    dups = 0
    for r in item_rows:
        k = (r[0], r[1])
        if k in seen:
            dups += 1
        seen.add(k)
    print("duplicate PK pairs      : %d" % dups)
    if dups:
        raise SystemExit("duplicate primary keys in source; refusing import")

    if args.dry_run:
        conn = sqlite3.connect(args.db)
        try:
            have_v = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='vendors'"
            ).fetchone()[0]
            have_i = conn.execute(
                "SELECT count(*) FROM sqlite_master "
                "WHERE type='table' AND name='vendor_sale_items'"
            ).fetchone()[0]
            cv = conn.execute("SELECT count(*) FROM vendors").fetchone()[0] if have_v else "-"
            ci = conn.execute("SELECT count(*) FROM vendor_sale_items").fetchone()[0] if have_i else "-"
        finally:
            conn.close()
        print("[dry-run] target tables exist: vendors=%s vendor_sale_items=%s" % (bool(have_v), bool(have_i)))
        print("[dry-run] current row counts  : vendors=%s sale_items=%s" % (cv, ci))
        print("[dry-run] would write         : vendors=%d sale_items=%d" % (len(vendor_rows), len(item_rows)))
        print("[dry-run] no writes performed")
        return 0

    conn = sqlite3.connect(args.db)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        ensure_schema(conn)
        with conn:  # single transaction; full replace = idempotent re-import
            conn.execute("DELETE FROM vendor_sale_items")
            conn.execute("DELETE FROM vendors")
            conn.executemany(
                "INSERT INTO vendors (vendor_hash, vendor_index, name, item_list_json) "
                "VALUES (?, ?, ?, ?)",
                vendor_rows,
            )
            conn.executemany(
                "INSERT INTO vendor_sale_items (vendor_hash, vendor_item_index, item_hash, "
                "quantity, currencies_json, action_json, category_index, "
                "display_category_index, minimum_level, maximum_level, "
                "inventory_bucket_hash, visibility_scope, purchasable_scope, "
                "socket_overrides_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                item_rows,
            )
        nv = conn.execute("SELECT count(*) FROM vendors").fetchone()[0]
        ni = conn.execute("SELECT count(*) FROM vendor_sale_items").fetchone()[0]
        orph = conn.execute(
            "SELECT count(*) FROM vendor_sale_items s "
            "LEFT JOIN vendors v ON v.vendor_hash = s.vendor_hash WHERE v.vendor_hash IS NULL"
        ).fetchone()[0]
    finally:
        conn.close()

    print("inserted vendors        : %d" % nv)
    print("inserted sale items     : %d" % ni)
    print("orphan sale items       : %d" % orph)
    if orph:
        raise SystemExit("referential integrity violated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
