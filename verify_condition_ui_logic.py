import asyncio
import aiohttp
import sys

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

async def main():
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("Logging in...")
        async with session.post(f"{BASE_URL}/token", data={"username": USERNAME, "password": PASSWORD}) as resp:
            if resp.status != 200:
                print(f"Login failed: {await resp.text()}")
                return
            token_data = await resp.json()
            token = token_data['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            print("Login successful.")

        # 2. Fetch a Product and a Category (for realistic IDs)
        product_id = "mock-product-id"
        category_id = "mock-category-id"
        
        try:
             async with session.get(f"{BASE_URL}/catalog/api/products?page=1&page_size=1", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['items']:
                        product_id = data['items'][0]['id']
                        print(f"Fetched real product ID: {product_id}")
        except Exception as e:
            print(f"Failed to fetch products: {e}")

        try:
             async with session.get(f"{BASE_URL}/catalog/api/categories/list?page=1&page_size=1", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['items']:
                        category_id = data['items'][0]['id']
                        print(f"Fetched real category ID via pagination: {category_id}")
        except Exception as e:
            print(f"Failed to fetch categories: {e}")

        # 3. Create Payment Constraint with specific conditions
        print("Creating Payment Constraint with PRODUCTS and PRODUCT_CATEGORY conditions...")
        constraint_data = {
            "name": "Condition Logic Test",
            "is_active": True,
            "payment_method_ids": ["cod"], # Mock
            "is_custom_error_enabled": False,
            "conditions": [
                {
                    "type": "PRODUCTS",
                    "operator": "IN",
                    "value": {"product_ids": [product_id]}
                },
                {
                    "type": "PRODUCT_CATEGORY",
                    "operator": "IN",
                    "value": {"mode": "include", "category_ids": [category_id]}
                }
            ]
        }

        async with session.post(f"{BASE_URL}/api/settings/constraints/payment", json=constraint_data, headers=headers) as resp:
            if resp.status not in [200, 201]:
                print(f"Creation failed: {await resp.text()}")
                sys.exit(1)
            created_constraint = await resp.json()
            constraint_id = created_constraint['id']
            print(f"Created constraint ID: {constraint_id}")

        # 4. Fetch and Verify
        print("Fetching constraint to verify data persistence...")
        async with session.get(f"{BASE_URL}/api/settings/constraints/payment/{constraint_id}", headers=headers) as resp:
            if resp.status != 200:
                print(f"Fetch failed: {await resp.text()}")
                sys.exit(1)
            fetched = await resp.json()
            
            conditions = fetched['conditions']
            prod_cond = next((c for c in conditions if c['type'] == 'PRODUCTS'), None)
            cat_cond = next((c for c in conditions if c['type'] == 'PRODUCT_CATEGORY'), None)

            if not prod_cond or prod_cond['value']['product_ids'][0] != product_id:
                print("FAILED: PRODUCTS condition data mismatch.")
                print(f"Expected: {[product_id]}, Got: {prod_cond['value'] if prod_cond else 'None'}")
            else:
                print("SUCCESS: PRODUCTS condition verified.")

            if not cat_cond or cat_cond['value']['category_ids'][0] != category_id or cat_cond['value']['mode'] != 'include':
                print("FAILED: PRODUCT_CATEGORY condition data mismatch.")
                print(f"Expected: include/[{category_id}], Got: {cat_cond['value'] if cat_cond else 'None'}")
            else:
                print("SUCCESS: PRODUCT_CATEGORY condition verified.")

        # 5. Clean up
        print("Deleting constraint...")
        async with session.delete(f"{BASE_URL}/api/settings/constraints/payment/{constraint_id}", headers=headers) as resp:
            if resp.status != 204:
                print("Delete failed.")
            else:
                print("Constraint deleted.")

if __name__ == "__main__":
    asyncio.run(main())
