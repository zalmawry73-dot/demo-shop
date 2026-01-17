import sqlite3
import json
import datetime

DB_PATH = "d:/Store/store_v2.db"

def update_schema():
    print(f"Connecting to {DB_PATH}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Drop table if exists to ensure clean slate (since it might have bad schema)
        print("Dropping existing legal_pages table to ensure schema correctness...")
        cursor.execute("DROP TABLE IF EXISTS legal_pages")
        
        # Check if table exists (it won't now, but keeping structure)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='legal_pages'")
        if not cursor.fetchone():
            print("Creating legal_pages table...")
            cursor.execute("""
                CREATE TABLE legal_pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(50) NOT NULL UNIQUE,
                    title_ar VARCHAR(255) NOT NULL,
                    title_en VARCHAR(255) NOT NULL,
                    content_ar TEXT,
                    content_en TEXT,
                    is_visible BOOLEAN DEFAULT 1,
                    is_customer_visible BOOLEAN DEFAULT 1,
                    locations JSON DEFAULT '["footer"]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX ix_legal_pages_slug ON legal_pages (slug)")
            print("Table created successfully.")
        else:
            print("Table 'legal_pages' already exists.")

        # Seed default data
        seed_data = [
            {
                "slug": "privacy-policy",
                "title_ar": "سياسة الخصوصية",
                "title_en": "Privacy Policy"
            },
            {
                "slug": "terms-conditions",
                "title_ar": "الشروط والأحكام",
                "title_en": "Terms & Conditions"
            },
            {
                "slug": "refund-policy",
                "title_ar": "سياسة الاستبدال والإرجاع",
                "title_en": "Refund Policy"
            },
            {
                "slug": "complaints",
                "title_ar": "الشكاوى والاقتراحات",
                "title_en": "Complaints & Suggestions"
            },
            {
                "slug": "licenses",
                "title_ar": "التراخيص",
                "title_en": "Licenses"
            }
        ]

        current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        for page in seed_data:
            cursor.execute("SELECT 1 FROM legal_pages WHERE slug = ?", (page["slug"],))
            if not cursor.fetchone():
                print(f"Seeding {page['slug']}...")
                cursor.execute("""
                    INSERT INTO legal_pages (slug, title_ar, title_en, content_ar, content_en, is_visible, is_customer_visible, locations, created_at, updated_at)
                    VALUES (?, ?, ?, '', '', 1, 1, '["footer"]', ?, ?)
                """, (page["slug"], page["title_ar"], page["title_en"], current_time, current_time))
        
        conn.commit()
        print("Schema update and seeding completed successfully.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    update_schema()
