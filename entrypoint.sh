#!/bin/sh
# Runs seed_users.py automatically on every container start,
# then launches Flask. Safe to run multiple times — skips
# anything that already exists in the DB.

echo "==> Running seed_users.py..."
python seed_users.py

# Initialize the SQLi challenge databases (secrets + flag)
echo "Initializing CTF challenge databases..."
python init_db.py

echo "==> Starting Flask..."
exec flask run