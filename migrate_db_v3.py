"""
Compatibility wrapper for running the migration script from the repository root.
"""

from src.migrate_db_v3 import *  # noqa: F401,F403

if __name__ == "__main__":
    from src.migrate_db_v3 import main
    main()
