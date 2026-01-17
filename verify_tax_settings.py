import asyncio
import aiohttp
import json

BASE_URL = "http://127.0.0.1:8000"

async def verify_tax_settings():
    async with aiohttp.ClientSession() as session:
        # 1. Login
        print("Logging in...")
        login_payload = {"username": "admin", "password": "admin123"} # Default credentials
        async with session.post(f"{BASE_URL}/token", data=login_payload) as resp:
            if resp.status != 200:
                print(f"Login failed: {resp.status} - {await resp.text()}")
                return
            token_data = await resp.json()
            access_token = token_data['access_token']
        
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        print("Login successful.")

        # 2. Update Store Tax Settings
        print("\nUpdating Store Tax Settings...")
        settings_update = {
            "is_vat_enabled": True,
            "prices_include_vat": True,
            "default_tax_rate": 15.0
        }
        async with session.put(f"{BASE_URL}/api/settings/store", json=settings_update, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data['is_vat_enabled'] and data['default_tax_rate'] == 15.0:
                    print("SUCCESS: Store settings updated.")
                else:
                    print(f"FAILURE: Data mismatch: {data}")
            else:
                print(f"FAILURE: Update store settings failed: {resp.status} - {await resp.text()}")

        # 3. Create Country Tax
        print("\nCreating Country Tax (SA)...")
        country_tax = {
            "country_code": "SA",
            "country_name": "Saudi Arabia",
            "tax_number": "3000111222333",
            "tax_rate": 15.0,
            "display_tax_number_in_footer": True,
            "display_vat_certificate_in_footer": True
        }
        country_tax_id = None
        async with session.post(f"{BASE_URL}/api/settings/tax/countries", json=country_tax, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                country_tax_id = data['id']
                print(f"SUCCESS: Country tax created with ID: {country_tax_id}")
            else:
                print(f"FAILURE: Create country tax failed: {resp.status} - {await resp.text()}")

        # 4. List Country Taxes
        print("\nListing Country Taxes...")
        async with session.get(f"{BASE_URL}/api/settings/tax/countries", headers=headers) as resp:
             if resp.status == 200:
                data = await resp.json()
                found = any(t['id'] == country_tax_id for t in data)
                if found:
                    print("SUCCESS: Created tax found in list.")
                else:
                    print("FAILURE: Created tax NOT found in list.")
             else:
                 print(f"FAILURE: List country tax failed: {resp.status}")

        # 5. Delete Country Tax
        if country_tax_id:
            print(f"\nDeleting Country Tax ID: {country_tax_id}...")
            async with session.delete(f"{BASE_URL}/api/settings/tax/countries/{country_tax_id}", headers=headers) as resp:
                if resp.status == 200:
                    print("SUCCESS: Country tax deleted.")
                else:
                    print(f"FAILURE: Delete failed: {resp.status}")

if __name__ == "__main__":
    asyncio.run(verify_tax_settings())
