import sqlite3
from pathlib import Path

# Tables Django creates by itself (these always have rows, so we skip them)
SYSTEM = {
    "django_migrations",
    "sqlite_sequence",
    "django_content_type",
    "auth_permission",
    "django_session",
    "django_admin_log",
    "django_site",
}

# Only READS the files. Nothing is changed or deleted.
for p in Path(r"C:\Cybexel").rglob("*.sqlite3"):
    if "venv" in p.parts:
        continue
    try:
        c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
        rows = []
        for (t,) in c.execute("select name from sqlite_master where type='table'"):
            if t in SYSTEM:
                continue
            n = c.execute(f'select count(*) from "{t}"').fetchone()[0]
            if n:
                rows.append(f"{t}={n}")
        print(p, "->", ", ".join(rows) if rows else "EMPTY")
        c.close()
    except Exception as e:
        print(p, "-> error:", e)