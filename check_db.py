import sqlite3

db_path = r"C:\Users\smnk2\.gemini\antigravity\conversations\912b22a2-2dc4-4b9b-9621-45477e4414c5.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    count = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"Table {t}: {count} rows")
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"  Columns: {cols}")
