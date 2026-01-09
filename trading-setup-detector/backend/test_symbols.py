#!/usr/bin/env python3
"""Test script to verify the symbols endpoint"""
import asyncio
import sys
from src.database import async_session
from src.binance.client import BinanceClient
from src.auth.models import User
from sqlalchemy import select

async def test_symbols_endpoint():
    print("Testing Binance symbols endpoint...\n")

    # Test 1: Check if BinanceClient works
    print("1. Testing BinanceClient directly:")
    client = BinanceClient()
    await client.connect()
    symbols = await client.get_all_usdt_symbols()
    print(f"   ✓ Got {len(symbols)} symbols from Binance")
    if symbols:
        print(f"   ✓ Sample symbols: {[s.symbol for s in symbols[:5]]}")
    await client.close()

    # Test 2: Check if there are users in the database
    print("\n2. Testing database users:")
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"   ✓ Found {len(users)} users in database")
        for user in users:
            print(f"   - {user.email} (active: {user.is_active})")

    print("\n✓ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_symbols_endpoint())
