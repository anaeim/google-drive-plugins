"""
demo.py
───────
A hands-on demo of every major feature in the Google Drive connector.
Run AFTER completing setup_auth.py.

Usage:
    python demo.py
"""

from connector import GoogleDriveConnector

def main():
    # ── Connect ──────────────────────────────────────────────────────────────
    conn = GoogleDriveConnector()
    conn.connect()

    # ── 1. List all files ────────────────────────────────────────────────────
    print("\n── 1. ALL FILES (most recent 15) ──")
    files = conn.list_files(page_size=15)
    conn.print_files(files)

    # ── 2. Search files ──────────────────────────────────────────────────────
    print("\n── 2. SEARCH for files named 'budget' ──")
    results = conn.search_files("budget")
    conn.print_files(results)

    # ── 3. Create a folder ───────────────────────────────────────────────────
    print("\n── 3. CREATE FOLDER ──")
    folder_id = conn.create_folder("Demo Folder")
    print(f"   Folder ID: {folder_id}")

    # ── 4. Create a Google Doc ───────────────────────────────────────────────
    print("\n── 4. CREATE GOOGLE DOC ──")
    doc_id = conn.create_doc("Demo Document", parent_id=folder_id)
    print(f"   Doc ID: {doc_id}")

    # ── 5. Append text to the Doc ────────────────────────────────────────────
    print("\n── 5. APPEND TEXT TO DOC ──")
    conn.append_to_doc(doc_id, "\nHello from the Google Drive Connector!")
    conn.append_to_doc(doc_id, "\nThis line was added automatically.")

    # ── 6. Read the Doc ──────────────────────────────────────────────────────
    print("\n── 6. READ DOC TEXT ──")
    text = conn.get_doc_text(doc_id)
    print(repr(text))

    # ── 7. Find-and-replace in the Doc ──────────────────────────────────────
    print("\n── 7. FIND & REPLACE IN DOC ──")
    conn.replace_doc_text(doc_id, "Hello", "Greetings")

    # ── 8. Create a Google Sheet ─────────────────────────────────────────────
    print("\n── 8. CREATE GOOGLE SHEET ──")
    sheet_id = conn.create_sheet("Demo Spreadsheet", parent_id=folder_id)
    print(f"   Sheet ID: {sheet_id}")

    # ── 9. Write data to the Sheet ───────────────────────────────────────────
    print("\n── 9. WRITE TO SHEET ──")
    conn.write_sheet(
        sheet_id,
        "Sheet1!A1",
        [
            ["Name", "Score", "Grade"],
            ["Alice", 95, "A"],
            ["Bob",   82, "B"],
            ["Carol", 78, "C"],
        ],
    )

    # ── 10. Read back from the Sheet ─────────────────────────────────────────
    print("\n── 10. READ FROM SHEET ──")
    rows = conn.read_sheet(sheet_id, "Sheet1!A1:C10")
    for row in rows:
        print("  ", row)

    # ── 11. Append a row ─────────────────────────────────────────────────────
    print("\n── 11. APPEND ROW TO SHEET ──")
    conn.append_to_sheet(sheet_id, "Sheet1!A1", [["Dave", 91, "A-"]])

    print("\n✅  Demo complete!")
    print(f"   Check your Drive – look for 'Demo Folder'")
    print(f"   Doc URL:   https://docs.google.com/document/d/{doc_id}/edit")
    print(f"   Sheet URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")

if __name__ == "__main__":
    main()
