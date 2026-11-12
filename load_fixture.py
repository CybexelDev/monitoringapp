import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "monitoring.settings")
django.setup()

from django.core.management import call_command
from django.db import connection
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)

# Safety check: this script must only run against the Render PostgreSQL database.
if connection.vendor != "postgresql":
    print("STOP: connected to", connection.vendor, "- not PostgreSQL. Nothing was loaded.")
    sys.exit(1)

# Turn off all signal handlers (notification signals etc.) for this one run,
# so the saved data is loaded exactly as it is, without creating extra rows.
for sig in (post_save, pre_save, m2m_changed, post_delete, pre_delete):
    sig.receivers = []
    if hasattr(sig, "sender_receivers_cache"):
        sig.sender_receivers_cache.clear()

print("Connected to PostgreSQL. Signals are off. Loading data.json ...")
call_command("loaddata", "data.json")
print("DONE")