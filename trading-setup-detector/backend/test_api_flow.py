#!/usr/bin/env python3
"""Test the full API flow: login -> get symbols"""
import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"

async def test_full_flow():
    async with httpx.AsyncClient() as client:
        print("Testing full API flow...\n")

        # Step 1: Try to get symbols without auth (should fail)
        print("1. Testing symbols endpoint without auth:")
        response = await client.get(f"{BASE_URL}/binance/symbols")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        # Step 2: Login
        print("2. Attempting login...")
        login_data = {
            "username": "test@test.com",  # Change this to your email
            "password": "test123"  # Change this to your password
        }
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   ✓ Login successful! Got token: {token[:20]}...\n")

            # Step 3: Get symbols with auth
            print("3. Testing symbols endpoint with auth:")
            response = await client.get(
                f"{BASE_URL}/binance/symbols",
                headers={"Authorization": f"Bearer {token}"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ Got {data['total']} symbols")
                print(f"   ✓ First 5: {[s['symbol'] for s in data['symbols'][:5]]}")
            else:
                print(f"   ✗ Error: {response.json()}")
        else:
            print(f"   ✗ Login failed: {response.json()}")
            print("\n   Please update the credentials in the script!")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
