import sqlite3

DB_PATH = "d:/Store/store_v2.db"

def add_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        columns_to_add = [
            ("store_desc", "VARCHAR(500)"),
            ("commercial_activity_type", "VARCHAR(50)"),
            ("commercial_name", "VARCHAR(255)"),
            ("commercial_registration_number", "VARCHAR(50)"),
            ("commercial_registration_name", "VARCHAR(255)"),
            ("is_manager_owner", "BOOLEAN DEFAULT 1"),
            ("owner_name", "VARCHAR(100)"),
            ("owner_phone", "VARCHAR(50)"),
            ("show_address_in_storefront", "BOOLEAN DEFAULT 0"),
            ("use_google_maps_location", "BOOLEAN DEFAULT 0"),
            ("timezone", "VARCHAR(50)"),
            ("address_street", "VARCHAR(255)"),
            ("address_city", "VARCHAR(100)"),
            ("address_country", "VARCHAR(100)"),
            ("address_lat", "FLOAT"),
            ("address_lng", "FLOAT")
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
