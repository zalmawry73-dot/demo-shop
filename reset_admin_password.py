
from app.core.security import get_password_hash
import sqlite3

def reset_password():
    new_password = "password"
    hashed = get_password_hash(new_password)
    
    conn = sqlite3.connect('store_v2.db')
    cursor = conn.cursor()
    
    cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'admin'", (hashed,))
    if cursor.rowcount > 0:
        print("Password updated for 'admin' to 'password'")
    else:
        print("User 'admin' not found.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_password()
