# -*- coding: utf-8 -*-
"""2a: the clean all-2 seed — the account-scope flags to all 12,300 indices value 2.
The proven pattern (FINDINGS 10.19): DELETE + INSERT, never INSERT OR REPLACE (the
table has NO unique constraint; the first attempt made 17,231 dupes). The other
scopes (profile/character/character_object) = untouched. Backup = a timestamped
copy of the flags table before the change (the rollback artifact)."""
import shutil
import sqlite3
import sys
import time

DB = r"RE_output\s1_accept\Sunrise\state.db"
ACCOUNT = "0x9EAA300100100100"
BANK_SIZE = 12300


def main():
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = DB + ".bak_flags_" + stamp
    shutil.copy2(DB, backup)
    print("backup: %s" % backup)

    db = sqlite3.connect(DB)
    cur = db.cursor()
    cur.execute("DELETE FROM flags WHERE scope='account'")
    rows = [(ACCOUNT, "account", i, 2) for i in range(BANK_SIZE)]
    cur.executemany(
        "INSERT INTO flags (account_id, scope, flag_index, value) VALUES (?,?,?,?)",
        rows)
    db.commit()

    total = cur.execute("SELECT COUNT(*) FROM flags").fetchone()[0]
    acct = cur.execute(
        "SELECT COUNT(*), MIN(flag_index), MAX(flag_index) FROM flags WHERE scope='account'"
    ).fetchone()
    hist = cur.execute("SELECT value, COUNT(*) FROM flags WHERE scope='account' GROUP BY value").fetchall()
    db.close()
    print("flags total rows: %d" % total)
    print("account scope: %d rows, indices %d..%d" % (acct[0], acct[1], acct[2]))
    print("account value histogram: %s" % hist)
    ok = acct[0] == BANK_SIZE and hist == [(2, BANK_SIZE)]
    print("SEED %s" % ("OK" if ok else "FAILED"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
