"""
example_usage.py — Walkthrough of the Google Drive Connector
=============================================================
Run this file to see a live demo of every major feature.
Requires the connector to be authenticated first (see README.md).
"""

from connector import GoogleDriveConnector


def main():
    # ── Connect ──────────────────────────────────────────────────────────────
    conn = GoogleDriveConnector()

    # ── 1. List files ─────────────────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("1. Listing your 10 most recently modified files")
    print("──────────────────────────────────────────────────")
    files = conn.list_files(max_results=10)
    for f in files:
        print(f"  • {f['name']}  ({f['mimeType'].split('.')[-1]})  id={f['id']}")

    # ── 2. Search files ───────────────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("2. Searching for files with 'report' in the name")
    print("──────────────────────────────────────────────────")
    results = conn.search_files("report", max_results=5)
    for f in results:
        print(f"  • {f['name']}")

    # ── 3. Create a folder ───────────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("3. Creating a folder called 'Demo Folder'")
    print("──────────────────────────────────────────────────")
    folder = conn.create_folder("Demo Folder")
    folder_id = folder["id"]
    print(f"  Created: {folder['name']}  id={folder_id}")
    print(f"  Link: {folder.get('webViewLink')}")

    # ── 4. Create a Google Doc ───────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("4. Creating a Google Doc inside the folder")
    print("──────────────────────────────────────────────────")
    doc = conn.create_google_doc(
        title="My Demo Document",
        parent_id=folder_id,
        initial_text="Hello from the Google Drive Connector!\n\nThis doc was created programmatically.\n",
    )
    doc_id = doc["documentId"]
    print(f"  Doc ID : {doc_id}")
    print(f"  Title  : {doc['title']}")

    # Read it back
    text = conn.read_doc_text(doc_id)
    print(f"  Content preview: {text[:80].strip()!r}")

    # Append more text
    conn.append_to_doc(doc_id, "\nAppended line via append_to_doc().\n")

    # Find-and-replace
    conn.replace_text_in_doc(doc_id, "Hello", "Hi there,")
    print("  Text replaced and appended successfully.")

    # ── 5. Create a Google Sheet ─────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("5. Creating a Google Sheet inside the folder")
    print("──────────────────────────────────────────────────")
    sheet = conn.create_google_sheet(
        title="My Demo Spreadsheet",
        parent_id=folder_id,
        sheet_names=["Sales", "Inventory"],
    )
    sheet_id = sheet["spreadsheetId"]
    print(f"  Sheet ID  : {sheet_id}")
    print(f"  Sheet URL : {sheet.get('spreadsheetUrl')}")

    # Write a header row and some data
    conn.write_sheet_range(
        sheet_id,
        "Sales!A1",
        [
            ["Date", "Product", "Units", "Revenue"],
            ["2026-09-01", "Widget A", 120, 2400],
            ["2026-09-02", "Widget B",  85, 1700],
        ],
    )

    # Append more rows
    conn.append_sheet_rows(
        sheet_id,
        "Sales!A1",
        [
            ["2026-09-03", "Widget C", 200, 5000],
            ["2026-09-04", "Widget A",  60, 1200],
        ],
    )

    # Read it back
    data = conn.read_sheet_range(sheet_id, "Sales!A1:D10")
    print(f"  Read {len(data)} row(s) from Sales sheet:")
    for row in data:
        print(f"    {row}")

    # ── 6. Share a file ───────────────────────────────────────────────────────
    # Uncomment and replace with a real email to test sharing:
    # conn.share_file(doc_id, "someone@example.com", role="writer")

    # ── 7. Clean up (optional) ────────────────────────────────────────────────
    print("\n──────────────────────────────────────────────────")
    print("Done! The demo folder, doc, and sheet are live in your Drive.")
    print("To delete the demo folder and everything in it, uncomment below:")
    print("──────────────────────────────────────────────────")
    # conn.delete_file(folder_id)  # deletes the folder + its contents


if __name__ == "__main__":
    main()
