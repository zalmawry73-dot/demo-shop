import sqlite3

def restore_tables():
    db_path = "d:/Store/store_v2.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables_to_restore = [
        ("inventory_items_old", "inventory_items"),
        ("stock_movements_old", "stock_movements"),
        ("stock_taking_items_old", "stock_taking_items")
    ]
    
    try:
        for old_name, new_name in tables_to_restore:
            print(f"Restoring {old_name} -> {new_name}")
            cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
            
        conn.commit()
        print("Tables restored successfully.")
        
    except Exception as e:
        print(f"Error restoring tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    restore_tables()
