import sqlite3

DB_PATH = "d:/Store/store_v2.db"

def migrate():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Create work_groups table
        print("Creating work_groups table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_groups (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100) UNIQUE,
                permissions JSON DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Add group_id to users table if it doesn't exist
        print("Checking users table for group_id...")
        cursor.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if "group_id" not in columns:
            print("Adding group_id column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN group_id INTEGER REFERENCES work_groups(id)")
        else:
            print("Column group_id already exists in users table.")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    migrate()
