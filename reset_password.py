#!/usr/bin/env python3
"""
VPN Store — Standalone Admin Password Reset Utility.
Usage:
    sudo python3 reset_password.py [new_password]
    sudo python3 reset_password.py admin 12345678
"""

import sys
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_FILE = BASE_DIR / "data" / "vpn_store.db"

def main():
    print("=" * 60)
    print("   🛡️ VPN Store — Admin Password Reset Utility")
    print("=" * 60)

    if not DB_FILE.exists():
        print(f"❌ Error: Database file not found at: {DB_FILE}")
        print("Please ensure VPN Store is installed first.")
        sys.exit(1)

    # Check bcrypt
    try:
        import bcrypt
    except ImportError:
        # Try importing from virtual environment if installed there
        venv_lib = BASE_DIR / ".venv" / "lib"
        found = False
        if venv_lib.exists():
            for p in venv_lib.glob("python*/site-packages"):
                sys.path.insert(0, str(p))
                try:
                    import bcrypt
                    found = True
                    break
                except ImportError:
                    pass
        if not found:
            print("❌ Error: 'bcrypt' module not found.")
            print("Run with venv python: /opt/vpn_store/.venv/bin/python reset_password.py [password]")
            sys.exit(1)

    args = sys.argv[1:]
    target_username = "admin"
    new_password = "admin"

    if len(args) == 1:
        new_password = args[0]
    elif len(args) >= 2:
        target_username = args[0]
        new_password = args[1]

    conn = sqlite3.connect(str(DB_FILE))
    cur = conn.cursor()

    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admins'")
    if not cur.fetchone():
        print("❌ Table 'admins' does not exist in database.")
        conn.close()
        sys.exit(1)

    # Find admins
    cur.execute("SELECT id, username FROM admins")
    admins = cur.fetchall()

    if not admins:
        print(f"⚠️ No admin account found. Creating new admin: '{target_username}'...")
        hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, 'superadmin')",
            (target_username, hashed)
        )
        conn.commit()
        conn.close()
        print(f"✅ Success! Admin created with:")
        print(f"   👤 Username: {target_username}")
        print(f"   🔑 Password: {new_password}")
        return

    admin_ids = [a[0] for a in admins if a[1] == target_username]
    if not admin_ids:
        # If target username doesn't match, use the first admin
        first_id, first_user = admins[0]
        print(f"ℹ️ User '{target_username}' not found. Using existing admin '{first_user}' (ID: {first_id}).")
        target_username = first_user
        target_id = first_id
    else:
        target_id = admin_ids[0]

    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cur.execute(
        "UPDATE admins SET password_hash = ? WHERE id = ?",
        (hashed, target_id)
    )
    conn.commit()
    conn.close()

    print(f"✅ Password successfully updated!")
    print(f"   👤 Username: {target_username}")
    print(f"   🔑 Password: {new_password}")
    print("\nYou can now log in to the web panel at:")
    print(f"   http://YOUR_SERVER_IP:8000")
    print("=" * 60)

if __name__ == "__main__":
    main()
