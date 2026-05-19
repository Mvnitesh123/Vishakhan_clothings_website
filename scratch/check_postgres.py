import os
import sys
import django

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vishakhan_clothings.settings')
django.setup()

from django.db import connection

print("Checking PostgreSQL extensions...")
with connection.cursor() as cursor:
    try:
        # Create extension if not exists
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        print("pg_trgm extension verified and enabled successfully!")
        
        # Check active extensions
        cursor.execute("SELECT extname FROM pg_extension;")
        extensions = [row[0] for row in cursor.fetchall()]
        print(f"Active database extensions: {extensions}")
    except Exception as e:
        print(f"Error checking/enabling pg_trgm extension: {e}")
