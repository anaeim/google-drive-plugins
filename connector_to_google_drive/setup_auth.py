"""
setup_auth.py
─────────────
Run this ONCE after setting GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.
It opens your browser, you sign in with ali.naeim.gdrive@gmail.com, grant
permissions, and a token.json is saved for all future runs.

Usage:
    python setup_auth.py
"""

from connector import GoogleDriveConnector

def main():
    print("=" * 60)
    print("  Google Drive – First-time Authentication Setup")
    print("=" * 60)
    print()
    print("A browser window will open. Sign in with your Google account.")
    print("After you grant permissions, this script will confirm the")
    print("connection and list your most recent Drive files.\n")

    conn = GoogleDriveConnector()
    conn.connect()

    print("\n── Your 10 most recent Drive files ──")
    files = conn.list_files(page_size=10)
    conn.print_files(files)
    print("\n✅  Setup complete! You can now use connector.py in your scripts.")

if __name__ == "__main__":
    main()
