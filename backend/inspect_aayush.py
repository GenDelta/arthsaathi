import sqlite3
conn = sqlite3.connect("arthsaathi.db")
c = conn.cursor()
c.execute("""
    SELECT u.name, up.*
    FROM users u 
    JOIN user_profiles up ON u.id = up.user_id 
    WHERE u.name LIKE '%Aayush%'
""")
rows = c.fetchall()
cols = [d[0] for d in c.description]
if rows:
    for row in rows:
        for col, val in zip(cols, row):
            print(f"  {col}: {val}")
        print()
else:
    print("No profile found for Aayush. Listing all users:")
    c.execute("SELECT id, name, phone_number FROM users")
    for r in c.fetchall():
        print(r)
conn.close()
