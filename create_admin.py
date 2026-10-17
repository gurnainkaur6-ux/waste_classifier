"""
Compatibility wrapper for running the admin script from the repository root.
"""

from src.create_admin import *  # noqa: F401,F403

if __name__ == "__main__":
    from src.create_admin import main
    main()
