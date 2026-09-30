import sqlite3
conn = sqlite3.connect("arthsaathi.db")
c = conn.cursor()
c.execute("SELECT DISTINCT scheme_type, COUNT(*) FROM schemes GROUP BY scheme_type ORDER BY COUNT(*) DESC LIMIT 20")
for row in c.fetchall():
    print(row)

print("\n--- Sample scheme_type values ---")
c.execute("SELECT scheme_type, state_name, scheme_name FROM schemes LIMIT 10")
for row in c.fetchall():
    print(row)
conn.close()
