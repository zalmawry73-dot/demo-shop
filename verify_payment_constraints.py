import aiohttp
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000"

async def test_payment_constraints():
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
        print("\nCreating Payment Constraint...")
        create_payload = {
            "name": "Test Payment Constraint",
            "is_active": True,
            "payment_method_ids": ["cod", "stripe"],
            "custom_error_message": "Payment method not available for these items.",
            "is_custom_error_enabled": True,
            "conditions": [
                {
                    "type": "CART_TOTAL",
                    "operator": "GT",
                    "value": {"min": 500, "max": None}
                }
            ]
        }
        async with session.post(f"{BASE_URL}/api/settings/constraints/payment", json=create_payload, headers=headers) as resp:
            if resp.status != 200:
                print(f"Create failed: {await resp.text()}")
                return
            created_data = await resp.json()
            constraint_id = created_data["id"]
            print(f"Created Constraint ID: {constraint_id}")
            assert created_data["name"] == "Test Payment Constraint"
            assert created_data["payment_method_ids"] == ["cod", "stripe"]
            assert len(created_data["conditions"]) == 1
            print("Create verified.")

        # 3. Get List
        print("\nFetching List...")
        async with session.get(f"{BASE_URL}/api/settings/constraints/payment", headers=headers) as resp:
            data = await resp.json()
            print(f"Found {len(data)} constraints.")
            assert any(c["id"] == constraint_id for c in data)
            print("List verified.")

        # 4. Update Constraint
        print("\nUpdating Constraint...")
        update_payload = {
            "name": "Updated Payment Constraint",
            "payment_method_ids": ["tamara", "tabby"],
            "conditions": [
                {
                    "type": "CART_QUANTITY",
                    "value": {"min": 2}
                },
                {
                    "type": "PRODUCT_TYPE",
                    "value": {"mode": "include", "product_type": "Digital"}
                }
            ]
        }
        async with session.put(f"{BASE_URL}/api/settings/constraints/payment/{constraint_id}", json=update_payload, headers=headers) as resp:
            if resp.status != 200:
                print(f"Update failed: {await resp.text()}")
                return
            updated_data = await resp.json()
            print("Updated data received:", json.dumps(updated_data, indent=2))
            assert updated_data["name"] == "Updated Payment Constraint"
            assert updated_data["payment_method_ids"] == ["tamara", "tabby"]
            assert len(updated_data["conditions"]) == 2
            print("Update verified.")

        # 5. Delete Constraint
        print("\nDeleting Constraint...")
        async with session.delete(f"{BASE_URL}/api/settings/constraints/payment/{constraint_id}", headers=headers) as resp:
            assert resp.status == 200
            print("Delete response 200 OK.")

        # 6. Verify Deletion
        print("\nVerifying Deletion...")
        async with session.get(f"{BASE_URL}/api/settings/constraints/payment/{constraint_id}", headers=headers) as resp:
            assert resp.status == 404
            print("Constraint not found as expected.")

        print("\n✅ All Payment Constraint Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_payment_constraints())
