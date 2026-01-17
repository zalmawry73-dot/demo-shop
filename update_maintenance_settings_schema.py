import sqlite3

DB_PATH = "d:/Store/store_v2.db"

def add_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        columns_to_add = [
            ("maintenance_mode_enabled", "BOOLEAN DEFAULT 0"),
            ("maintenance_type", "VARCHAR(50) DEFAULT 'fully_closed'"),
            ("maintenance_period_type", "VARCHAR(50) DEFAULT 'unlimited'"),
            ("maintenance_minutes", "INTEGER"),
            ("maintenance_hours", "INTEGER"),
            ("maintenance_start_at", "TIMESTAMP"),
            ("maintenance_end_at", "TIMESTAMP"),
            ("maintenance_show_countdown", "BOOLEAN DEFAULT 0"),
            ("maintenance_title_ar", "VARCHAR(255)"),
            ("maintenance_title_en", "VARCHAR(255)"),
            ("maintenance_message_ar", "VARCHAR(1000)"),
            ("maintenance_message_en", "VARCHAR(1000)")
        ]

        # Get existing columns
        cursor.execute("PRAGMA table_info(store_settings)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        for col_name, col_type in columns_to_add:
            if col_name not in existing_cols:
                print(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE store_settings ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists.")

        conn.commit()
        print("Schema update completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    add_columns()
