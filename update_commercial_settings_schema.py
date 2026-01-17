import sqlite3

DB_PATH = "d:/Store/store_v2.db"

def add_commercial_columns():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        columns_to_add = [
            ("national_id", "VARCHAR(50)"),
            ("branches_count", "INTEGER"),
            ("employees_count", "INTEGER"),
            ("electronic_activity", "VARCHAR(100)"),
            ("electronic_activity_type", "VARCHAR(100)"),
            ("national_id_image", "VARCHAR(500)"),
            ("tax_certificate_image", "VARCHAR(500)"),
            ("freelance_certificate_image", "VARCHAR(500)"),
            ("ecommerce_auth_certificate_image", "VARCHAR(500)"),
            ("bank_certificate_image", "VARCHAR(500)"),
            ("activity_license_image", "VARCHAR(500)"),
            ("commercial_registration_image_url", "VARCHAR(500)")
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
    add_commercial_columns()
