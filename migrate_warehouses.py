
import sqlite3
import os

DB_PATH = "store_v2.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns = [
        ("name_en", "TEXT"),
        ("country", "TEXT DEFAULT 'السعودية'"),
        ("city", "TEXT"),
        ("district", "TEXT"),
        ("street", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL")
    ]

    print("Migrating warehouses table...")
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE warehouses ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
