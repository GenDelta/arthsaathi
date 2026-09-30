import sqlite3
conn = sqlite3.connect("arthsaathi.db")
c = conn.cursor()
c.execute("SELECT COUNT(*), MIN(occurred_at), MAX(occurred_at), MIN(created_at) FROM transactions")
row = c.fetchone()
print(f"Count: {row[0]}, Min date: {row[1]}, Max date: {row[2]}, First created: {row[3]}")
c.execute("SELECT type, category, amount, description, occurred_at FROM transactions LIMIT 5")
for r in c.fetchall(): print(r)
conn.close()
