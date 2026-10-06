import sqlite3

db_path = r"C:\Users\smnk2\.gemini\antigravity\conversations\912b22a2-2dc4-4b9b-9621-45477e4414c5.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

rows = c.execute("SELECT idx, step_type, status, permissions FROM steps ORDER BY idx DESC LIMIT 10").fetchall()
for r in rows:
    print(r)
