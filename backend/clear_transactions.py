import sqlite3
conn = sqlite3.connect("arthsaathi.db")
conn.execute("DELETE FROM transactions")
conn.commit()
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM transactions")
print("Rows remaining:", c.fetchone()[0])
conn.close()
