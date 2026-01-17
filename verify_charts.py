import asyncio
import sys
import os
import requests

sys.path.append(os.getcwd())
from auth_utils import create_access_token
from main import app
from database import AsyncSessionLocal
from models import User, Order
from sqlalchemy import select

async def verify_chart_api():
    print("Verifying Sales Chart Endpoint...")
    
    # 1. Get Token (Simulate Admin)
    token = create_access_token(data={"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # Can't easily use requests against FastAPI app instance without running server.
    # But we can import the endpoint function and call it ensuring dependencies are mocked or used manually.
    # OR we can assume we rely on manual check mostly, but let's try to invoke the DB logic used.
    
    print(" - Token generated.")
    
    async with AsyncSessionLocal() as session:
        # Check if we get data from DB query logic
        from main import get_sales_chart_data
        # We need to mock dependency injection outcome
        # But wait, get_sales_chart_data is an async function expecting db session.
        
        try:
            data = await get_sales_chart_data(db=session, current_user="admin")
            print(f" - API Data received: {data}")
            
            assert "labels" in data
            assert "data" in data
            assert isinstance(data["labels"], list)
            assert isinstance(data["data"], list)
            
            print(" - Structure Valid: OK")
        except Exception as e:
            print(f" - API Logic Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify_chart_api())
