"""
migrate_db_v3.py
----------------
Database migration to add image_filename column for image upload feature.

Usage:
    python src/migrate_db_v3.py
"""
import os
import sqlite3

# Get database path
INSTANCE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "waste.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        print("Run the app first to create initial database.")
        return

    print("🔧 Migrating database for image upload feature...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        try:
            cursor.execute("SELECT image_filename FROM predictions LIMIT 1")
            print("✓ Column 'image_filename' already exists")
        except sqlite3.OperationalError:
            print("➕ Adding 'image_filename' column...")
            cursor.execute("ALTER TABLE predictions ADD COLUMN image_filename TEXT")
            print("✓ Added 'image_filename' column")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nImage upload feature is now enabled!")
        print("  • Users can upload images with predictions")
        print("  • Images stored in static/uploads/")
        print("  • Images visible in history and results")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def main():
    migrate()


if __name__ == "__main__":
    main()
