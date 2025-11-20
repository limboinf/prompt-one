"""
Migration script to update Prompt table:
- Remove unique constraint from 'name' column
- Add unique constraint on ('name', 'version') combination

Run this script to migrate existing database to support multiple versions per prompt name.
"""
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

def migrate():
    print("Starting migration: Add version unique constraint...")

    with engine.begin() as conn:
        # Check database type
        db_url = str(engine.url)

        if 'sqlite' in db_url:
            print("Detected SQLite database")
            # SQLite doesn't support dropping constraints directly
            # We need to recreate the table

            # 1. Create a new table with the correct schema
            conn.execute(text("""
                CREATE TABLE t_prompt_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(128) NOT NULL,
                    display_name VARCHAR(128) NOT NULL,
                    description VARCHAR(255),
                    version VARCHAR(32) NOT NULL DEFAULT 'v1',
                    template TEXT NOT NULL,
                    variables_meta JSON,
                    created_by VARCHAR(64),
                    comment VARCHAR(255),
                    is_enabled BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (name, version)
                )
            """))

            # 2. Copy data from old table to new table
            conn.execute(text("""
                INSERT INTO t_prompt_new
                SELECT * FROM t_prompt
            """))

            # 3. Drop old table
            conn.execute(text("DROP TABLE t_prompt"))

            # 4. Rename new table to original name
            conn.execute(text("ALTER TABLE t_prompt_new RENAME TO t_prompt"))

            print("SQLite migration completed successfully")

        elif 'postgresql' in db_url:
            print("Detected PostgreSQL database")
            # PostgreSQL migration

            # 1. Drop unique constraint on name (if exists)
            try:
                conn.execute(text("""
                    ALTER TABLE t_prompt DROP CONSTRAINT IF EXISTS t_prompt_name_key
                """))
                print("Dropped unique constraint on 'name' column")
            except Exception as e:
                print(f"Note: Could not drop unique constraint (may not exist): {e}")

            # 2. Add unique constraint on (name, version)
            conn.execute(text("""
                ALTER TABLE t_prompt
                ADD CONSTRAINT uq_prompt_name_version UNIQUE (name, version)
            """))

            print("PostgreSQL migration completed successfully")

        elif 'mysql' in db_url:
            print("Detected MySQL database")
            # MySQL migration

            # 1. Drop unique index on name (if exists)
            try:
                conn.execute(text("""
                    ALTER TABLE t_prompt DROP INDEX name
                """))
                print("Dropped unique index on 'name' column")
            except Exception as e:
                print(f"Note: Could not drop unique index (may not exist): {e}")

            # 2. Add unique constraint on (name, version)
            conn.execute(text("""
                ALTER TABLE t_prompt
                ADD CONSTRAINT uq_prompt_name_version UNIQUE (name, version)
            """))

            print("MySQL migration completed successfully")

        else:
            print(f"Warning: Unknown database type: {db_url}")
            print("Please manually update the database schema")
            return

    print("Migration completed!")
    print("\nNext steps:")
    print("1. Verify the migration by checking the database schema")
    print("2. You can now create multiple versions of the same prompt name")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
