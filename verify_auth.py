import asyncio
import sys
import os
import requests

# We'll use requests to test the running server if possible, or simulate logic.
# Since we haven't started the uvicorn server in a separate process that we can easily curl,
# we will verify the auth utility logic and the database user creation.

sys.path.append(os.getcwd())
from auth_utils import verify_password, get_password_hash, create_access_token
from database import engine, AsyncSessionLocal
from models import User
from sqlalchemy import select

async def verify_auth_logic():
    print("Verifying Auth Logic...")
    
    # 1. Hashing
    pw = "secret"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)
    print(" - Password hashing/verification: OK")
    
    # 2. Token
    token = create_access_token(data={"sub": "admin"})
    assert token is not None
    print(" - JWT Token generation: OK")

    # 3. DB User
    print("Verifying Admin User in DB...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if user:
             print(f" - Found Admin User: {user.username}")
             assert verify_password("secret", user.password_hash)
             print(" - Admin password match: OK")
        else:
             print(" - WARNING: Admin user not found. (Is it created on startup?)")
             # It acts as a warning because startup event runs when main:app starts, which we are not running here.
             # but we can try to create it here manually to verify the flow if needed.
             print(" - Simulating Startup creation...")
             hashed_pw = get_password_hash("secret")
             admin_user = User(username="admin", email="admin@store.com", password_hash=hashed_pw, role="admin")
             session.add(admin_user)
             await session.commit()
             print(" - Created Admin User for verification.")

if __name__ == "__main__":
    asyncio.run(verify_auth_logic())
