
import sqlite3
import os

def apply_migration():
    db_path = 'store_v2.db'
    print(f"Connecting to {db_path} (Absolute: {os.path.abspath(db_path)})")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_templates'")
        if not cursor.fetchone():
            print("Table 'notification_templates' does NOT exist. Creating...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER DEFAULT 1,
                event_type VARCHAR(50) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                is_enabled BOOLEAN DEFAULT 1,
                message_template_ar TEXT,
                message_template_en TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
        else:
            print("Table 'notification_templates' already exists.")

        # Count records
        cursor.execute("SELECT count(*) FROM notification_templates")
        count = cursor.fetchone()[0]
        print(f"Current record count: {count}")
        
        if count == 0:
            events = [
                'order_created', 'order_processing', 'order_ready', 
                'order_shipped', 'order_delivered', 'order_completed', 'order_cancelled'
            ]
            channels = ['sms', 'whatsapp']
            
            for event in events:
                for channel in channels:
                    cursor.execute("""
                        INSERT INTO notification_templates (event_type, channel, is_enabled, message_template_ar, message_template_en)
                        VALUES (?, ?, 1, '', '')
                    """, (event, channel))
            print("Inserted default templates.")
        else:
            print("Data already exists. Sample:")
            cursor.execute("SELECT id, event_type, channel FROM notification_templates LIMIT 5")
            for row in cursor.fetchall():
                print(row)

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_migration()
