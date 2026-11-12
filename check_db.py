import sqlite3

c = sqlite3.connect("db.sqlite3")
for (t,) in c.execute("select name from sqlite_master where type='table'").fetchall():
    n = c.execute(f'select count(*) from "{t}"').fetchone()[0]
    if n:
        print(t, n)