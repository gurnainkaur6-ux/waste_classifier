"""
Compatibility wrapper for running the script from the repository root.
"""

from src.generate_data import *  # noqa: F401,F403

if __name__ == "__main__":
    from src.generate_data import main
    main()
