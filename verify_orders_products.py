
import asyncio
import aiohttp

API_URL = "http://127.0.0.1:8000"

async def test_orders_products_settings():
    async with aiohttp.ClientSession() as session:
        # 0. Login
        print("\n--- Logging in ---")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        async with session.post(f"{API_URL}/token", data=login_data) as resp:
            if resp.status != 200:
                print(f"Login failed: {await resp.text()}")
                return
            token_data = await resp.json()
            access_token = token_data["access_token"]
            print("Login successful.")

        headers = {"Authorization": f"Bearer {access_token}"}

        # 1. Test Order Settings
        print("\n--- Testing Order Settings ---")
        
        # Get initial
        async with session.get(f"{API_URL}/api/settings/orders", headers=headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            print("Initial Order Settings:", data)

        # Update
        new_order_settings = {
            "is_guest_checkout_enabled": False,
            "min_order_limit_enabled": True,
            "min_order_limit": 50.0
        }
        async with session.put(f"{API_URL}/api/settings/orders", json=new_order_settings, headers=headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            print("Updated Order Settings:", data)
            assert data["is_guest_checkout_enabled"] == False
            assert data["min_order_limit_enabled"] == True
            assert data["min_order_limit"] == 50.0

        # Verify Persistence
        async with session.get(f"{API_URL}/api/settings/orders", headers=headers) as resp:
             data = await resp.json()
             assert data["is_guest_checkout_enabled"] == False

        # 2. Test Product Settings
        print("\n--- Testing Product Settings ---")

        # Get initial
        async with session.get(f"{API_URL}/api/settings/products", headers=headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            print("Initial Product Settings:", data)

        # Update
        new_product_settings = {
            "show_similar_products": False,
            "similar_products_limit": 8
        }
        async with session.put(f"{API_URL}/api/settings/products", json=new_product_settings, headers=headers) as resp:
            assert resp.status == 200
            data = await resp.json()
            print("Updated Product Settings:", data)
            assert data["show_similar_products"] == False
            assert data["similar_products_limit"] == 8

        # Verify Persistence
        async with session.get(f"{API_URL}/api/settings/products", headers=headers) as resp:
             data = await resp.json()
             assert data["show_similar_products"] == False

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_orders_products_settings())
