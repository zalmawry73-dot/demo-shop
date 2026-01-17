
import asyncio
import requests
from database import AsyncSessionLocal
from models import User
from auth_utils import create_access_token
from datetime import timedelta

SERVER_URL = "http://127.0.0.1:8000"

async def get_admin_token():
    # Generate token directly to avoid login dependency for this test
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=timedelta(minutes=5)
    )
    return access_token

def test_pos_products_api():
    print("1. Getting Token...")
    token = asyncio.run(get_admin_token())
    headers = {"Authorization": f"Bearer {token}"}
    
    print("2. Fetching All Products...")
    res = requests.get(f"{SERVER_URL}/api/pos/products", headers=headers)
    if res.status_code == 200:
        data = res.json()
        print(f" - Success. Found {len(data)} products.")
        if len(data) > 0:
            print(f" - Sample: {data[0]}")
    else:
        print(f" - FAILED: {res.text}")
        return

    print("\n3. Testing Search Filter ('POS')...")
    res_search = requests.get(f"{SERVER_URL}/api/pos/products?search=POS", headers=headers)
    if res_search.status_code == 200:
        data = res_search.json()
        print(f" - Found {len(data)} matches.")
        for p in data:
            if "POS" not in p['name'] and "POS" not in p.get('sku', ''):
                 print(f"   [WARN] Unexpected result: {p['name']}")
    else:
        print(f" - FAILED: {res_search.text}")

if __name__ == "__main__":
    try:
        test_pos_products_api()
    except Exception as e:
        print(f"Error: {e}")
