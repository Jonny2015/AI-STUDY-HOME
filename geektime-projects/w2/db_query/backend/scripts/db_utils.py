"""Database utility scripts for managing the SQLite database."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import aiosqlite
from app.config import settings


async def init_database() -> None:
    """Initialize the database with tables."""
    settings.ensure_database_dir()
    
    async with aiosqlite.connect(settings.database_path) as db:
        # Create databases table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                name TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                db_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_connected_at TEXT
            )
        """)

        # Create metadata table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                db_name TEXT NOT NULL,
                schema_name TEXT NOT NULL,
                table_name TEXT NOT NULL,
                table_type TEXT NOT NULL,
                column_name TEXT NOT NULL,
                data_type TEXT NOT NULL,
                is_nullable INTEGER NOT NULL,
                is_primary_key INTEGER NOT NULL,
                metadata_extracted_at TEXT NOT NULL,
                PRIMARY KEY (db_name, schema_name, table_name, column_name),
                FOREIGN KEY (db_name) REFERENCES databases(name) ON DELETE CASCADE
            )
        """)

        # Create indexes
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_db_name
            ON metadata(db_name)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_table_name
            ON metadata(table_name)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_schema_table
            ON metadata(schema_name, table_name)
        """)

        await db.commit()
    print(f"✓ 数据库已初始化: {settings.database_path}")


async def reset_database() -> None:
    """Reset the database by dropping all tables and recreating them."""
    settings.ensure_database_dir()
    
    async with aiosqlite.connect(settings.database_path) as db:
        # Drop tables
        await db.execute("DROP TABLE IF EXISTS metadata")
        await db.execute("DROP TABLE IF EXISTS databases")
        await db.commit()
    
    # Reinitialize
    await init_database()
    print("✓ 数据库已重置")


async def clean_database() -> None:
    """Clean all data from the database but keep table structure."""
    async with aiosqlite.connect(settings.database_path) as db:
        await db.execute("DELETE FROM metadata")
        await db.execute("DELETE FROM databases")
        await db.commit()
    print("✓ 数据库数据已清理")


async def show_database_info() -> None:
    """Show database information."""
    db_path = settings.database_path
    
    if not db_path.exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return
    
    # File size
    size = db_path.stat().st_size
    size_mb = size / (1024 * 1024)
    
    print(f"数据库位置: {db_path}")
    print(f"文件大小: {size_mb:.2f} MB ({size:,} bytes)")
    
    async with aiosqlite.connect(db_path) as db:
        # Count databases
        cursor = await db.execute("SELECT COUNT(*) FROM databases")
        db_count = (await cursor.fetchone())[0]
        
        # Count metadata entries
        cursor = await db.execute("SELECT COUNT(*) FROM metadata")
        metadata_count = (await cursor.fetchone())[0]
        
        # List databases
        cursor = await db.execute("""
            SELECT name, db_type, created_at, last_connected_at 
            FROM databases 
            ORDER BY created_at
        """)
        databases = await cursor.fetchall()
        
        print(f"\n已存储的数据库连接: {db_count}")
        print(f"元数据条目: {metadata_count}")
        
        if databases:
            print("\n数据库列表:")
            for name, db_type, created_at, last_connected_at in databases:
                print(f"  - {name} ({db_type})")
                print(f"    创建时间: {created_at}")
                if last_connected_at:
                    print(f"    最后连接: {last_connected_at}")


async def backup_database(backup_path: str = None) -> None:
    """Backup the database to a file."""
    db_path = settings.database_path
    
    if not db_path.exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return
    
    if backup_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = db_path.parent / f"db_query_backup_{timestamp}.db"
    else:
        backup_path = Path(backup_path)
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    
    size = backup_path.stat().st_size
    size_mb = size / (1024 * 1024)
    
    print(f"✓ 数据库已备份到: {backup_path}")
    print(f"  备份文件大小: {size_mb:.2f} MB")


async def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("用法: python db_utils.py <command>")
        print("可用命令:")
        print("  init    - 初始化数据库")
        print("  reset   - 重置数据库（删除所有数据并重新创建表）")
        print("  clean   - 清理数据库（删除所有数据但保留表结构）")
        print("  info    - 显示数据库信息")
        print("  backup  - 备份数据库")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "init":
            await init_database()
        elif command == "reset":
            confirm = input("确定要重置数据库吗？这将删除所有数据！(yes/no): ")
            if confirm.lower() == "yes":
                await reset_database()
            else:
                print("操作已取消")
        elif command == "clean":
            confirm = input("确定要清理数据库吗？这将删除所有数据！(yes/no): ")
            if confirm.lower() == "yes":
                await clean_database()
            else:
                print("操作已取消")
        elif command == "info":
            await show_database_info()
        elif command == "backup":
            backup_path = sys.argv[2] if len(sys.argv) > 2 else None
            await backup_database(backup_path)
        else:
            print(f"未知命令: {command}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

