#!/usr/bin/env python3
from __future__ import annotations
import os
import psycopg

url = os.environ.get("DATABASE_URL", "")
if not url:
    raise SystemExit("DATABASE_URL is missing")
with psycopg.connect(url) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM recipe")
        print(f"PostgreSQL connection successful. Recipes: {cursor.fetchone()[0]}")
