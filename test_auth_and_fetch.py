
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_flow():
    # 1. Login
    print("Testing Login...")
    try:
        # Check /token endpoint with form data
        resp = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "secret"}) 
        
        if resp.status_code != 200:
             # Try 'password'
             resp = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "password"})
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    if resp.status_code != 200:
        print(f"Login Failed: {resp.status_code} {resp.text}")
        return

    data = resp.json()
    token = data.get("access_token")
    print(f"Got Token: {token[:10]}...")

    # 2. Fetch Templates
    print("Fetching Templates...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/api/settings/notifications/templates", headers=headers)
    
    if resp.status_code == 200:
        templates = resp.json()
        print(f"Success! Found {len(templates)} templates.")
        print(templates)
    else:
        print(f"Fetch Failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    test_flow()
