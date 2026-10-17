"""
create_admin.py
---------------
Create an admin account, or promote an existing user to admin.

Usage:
    python create_admin.py <username> <email> [password]

If the password is omitted you will be asked for it (hidden typing).
If the username already exists, that user is made admin (password unchanged).
"""
import getpass
import sqlite3
import sys

from werkzeug.security import generate_password_hash

from app import app
import db


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    username, email = sys.argv[1], sys.argv[2].lower()
    with app.app_context():
        conn = db.get_db()
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            conn.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (existing["id"],))
            conn.commit()
            print(f"'{username}' is now an admin.")
            return

        password = sys.argv[3] if len(sys.argv) > 3 else getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            sys.exit(1)
        try:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
                (username, email, generate_password_hash(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            print("That email is already used by another account.")
            sys.exit(1)
        print(f"Admin '{username}' created.")


if __name__ == "__main__":
    main()
