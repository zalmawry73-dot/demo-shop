import aiohttp
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_shipping_constraints():
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("Logging in...")
        login_data = {"username": "admin", "password": "admin123"}
        async with session.post(f"{BASE_URL}/token", data=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {await resp.text()}")
                return
            token_data = await resp.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            print("Login successful.")

        # 2. Create Constraint
        print("\nCreating Shipping Constraint...")
        create_payload = {
            "name": "Test Constraint",
            "is_active": True,
            "shipping_company_ids": ["aramex", "smsa"],
            "custom_error_message": "Not available here.",
            "is_custom_error_enabled": True,
            "conditions": [
                {
                    "type": "CART_TOTAL",
                    "operator": "GT",
                    "value": {"min": 100, "max": 500}
                }
            ]
        }
        async with session.post(f"{BASE_URL}/api/settings/constraints/shipping", json=create_payload, headers=headers) as resp:
            if resp.status != 200:
                print(f"Create failed: {await resp.text()}")
                return
            created_data = await resp.json()
            constraint_id = created_data["id"]
            print(f"Created Constraint ID: {constraint_id}")
            assert created_data["name"] == "Test Constraint"
            assert len(created_data["conditions"]) == 1
            print("Create verified.")

        # 3. Get List
        print("\nFetching List...")
        async with session.get(f"{BASE_URL}/api/settings/constraints/shipping", headers=headers) as resp:
            data = await resp.json()
            print(f"Found {len(data)} constraints.")
            assert any(c["id"] == constraint_id for c in data)
            print("List verified.")

        # 4. Update Constraint
        print("\nUpdating Constraint...")
        update_payload = {
            "name": "Updated Constraint Name",
            "shipping_company_ids": ["dhl"],
            "conditions": [
                {
                    "type": "CART_QUANTITY",
                    "value": {"min": 5}
                },
                {
                    "type": "PRODUCTS",
                    "value": {"product_ids": [1, 2, 3]}
                },
                {
                    "type": "ORDER_TIME",
                    "value": {"days": [0, 4, 6], "start_time": "09:00", "end_time": "17:00"}
                },
                {
                    "type": "SALES_CHANNEL",
                    "value": {"channels": ["app", "pos"]}
                },
                {
                    "type": "CART_WEIGHT",
                    "value": {"min": 2.5, "max": 15.0}
                },
                {
                    "type": "CUSTOMER_GROUPS",
                    "value": {"mode": "exclude", "group_ids": [101]}
                },
                {
                    "type": "PRODUCT_CATEGORY",
                    "value": {"mode": "include", "category_ids": [55, 66]}
                },
                {
                    "type": "PRODUCT_TYPE",
                    "value": {"mode": "include", "product_type": "Physical"}
                },
                {
                    "type": "COUPONS",
                    "value": {"mode": "exclude", "coupons": ["TEST_CODE"]}
                },
                {
                    "type": "CUSTOMER_LOCATION",
                    "value": {"mode": "include", "country": "SA", "city": "Riyadh"}
                },
                {
                    "type": "CUSTOMER_ORDER_COUNT",
                    "value": {"max": 10}
                },
                {
                    "type": "CUSTOMER_CANCELLED_ORDER_COUNT",
                    "value": {"min": 2}
                }
            ]
        }
        async with session.put(f"{BASE_URL}/api/settings/constraints/shipping/{constraint_id}", json=update_payload, headers=headers) as resp:
            if resp.status != 200:
                print(f"Update failed: {await resp.text()}")
                return
            updated_data = await resp.json()
            print("Updated data received:", json.dumps(updated_data, indent=2))
            assert updated_data["name"] == "Updated Constraint Name"
            assert updated_data["shipping_company_ids"] == ["dhl"]
            assert len(updated_data["conditions"]) == 12
            print("Update verified.")

        # 5. Delete Constraint
        print("\nDeleting Constraint...")
        async with session.delete(f"{BASE_URL}/api/settings/constraints/shipping/{constraint_id}", headers=headers) as resp:
            assert resp.status == 200
            print("Delete response 200 OK.")

        # 6. Verify Deletion
        print("\nVerifying Deletion...")
        async with session.get(f"{BASE_URL}/api/settings/constraints/shipping/{constraint_id}", headers=headers) as resp:
            assert resp.status == 404
            print("Constraint not found as expected.")

        print("\n✅ All Shipping Constraint Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_shipping_constraints())
