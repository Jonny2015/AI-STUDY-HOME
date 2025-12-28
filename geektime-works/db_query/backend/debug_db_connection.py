#!/usr/bin/env python3
"""Debug script to test database connection issue."""

import asyncio
import asyncpg
from urllib.parse import urlparse
import traceback

async def test_direct_connection():
    """Test direct connection with asyncpg."""
    url = 'postgresql://postgres:postgres@localhost:5432/testdb'
    print(f"Testing direct connection with URL: {url}")

    try:
        conn = await asyncpg.connect(url)
        await conn.close()
        print("✅ Direct connection successful!")
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()

async def test_url_parsing():
    """Test URL parsing step by step."""
    url = 'postgresql://postgres:postgres@localhost:5432/testdb'
    print(f"\nTesting URL parsing: {url}")

    try:
        parsed = urlparse(url)
        print(f"  Scheme: {parsed.scheme}")
        print(f"  Hostname: {parsed.hostname}")
        print(f"  Port: {parsed.port}")
        print(f"  Username: {parsed.username}")
        print(f"  Password: {parsed.password}")
        print(f"  Path: {parsed.path}")

        # Test building connection string
        if parsed.port:
            host_with_port = f"{parsed.hostname}:{parsed.port}"
        else:
            host_with_port = parsed.hostname

        print(f"  Host with port: {host_with_port}")

        # Build DSN manually
        dsn = f"postgresql://{parsed.username}:{parsed.password}@{host_with_port}{parsed.path}"
        print(f"  Manual DSN: {dsn}")

    except Exception as e:
        print(f"❌ URL parsing failed: {e}")
        traceback.print_exc()

async def test_pool_creation():
    """Test connection pool creation."""
    url = 'postgresql://postgres:postgres@localhost:5432/testdb'
    print(f"\nTesting connection pool creation with URL: {url}")

    try:
        pool = await asyncpg.create_pool(
            url,
            min_size=1,
            max_size=1,
            command_timeout=60,
        )
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        await pool.close()
        print("✅ Pool creation successful!")
    except Exception as e:
        print(f"❌ Pool creation failed: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("Database Connection Debug Script")
    print("=" * 40)

    await test_url_parsing()
    await test_direct_connection()
    await test_pool_creation()

if __name__ == "__main__":
    asyncio.run(main())