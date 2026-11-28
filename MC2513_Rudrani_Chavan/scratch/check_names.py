import sqlite3

conn = sqlite3.connect('data/nutrimate.db')
cursor = conn.cursor()

print("Poha search:")
for row in cursor.execute("SELECT name FROM meals WHERE name LIKE '%Poha%'").fetchall():
    print("  ", row[0])

print("\nPaneer search:")
for row in cursor.execute("SELECT name FROM meals WHERE name LIKE '%Paneer%'").fetchall():
    print("  ", row[0])
