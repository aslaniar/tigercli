# -*- coding: utf-8 -*-
"""2a probe: the s1_accept flags table state (the schema + the row census)."""
import sqlite3

DB = r"RE_output\s1_accept\Sunrise\state.db"

db = sqlite3.connect(DB)
cur = db.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%flag%'")
tables = [r[0] for r in cur.fetchall()]
print("flag tables:", tables)
for t in tables:
    n = cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
    print("%s rows: %d" % (t, n))
    cols = cur.execute("PRAGMA table_info(%s)" % t).fetchall()
    print("  schema:", [(c[1], c[2]) for c in cols])
    if n:
        rows = cur.execute("SELECT * FROM %s LIMIT 3" % t).fetchall()
        for r in rows:
            print("  row:", r)
        hist = cur.execute(
            "SELECT value, COUNT(*) FROM %s GROUP BY value" % t).fetchall()
        print("  value histogram:", hist[:6], "..." if len(hist) > 6 else "")
db.close()
