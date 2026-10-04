# Google Drive Plugins

You can use these plugins to connect to your Google Drive, then create and edit Docs, Sheets, and Slides.

This repo is a small connector (`connector.py`) that signs in with OAuth, then talks to Drive, Docs, Sheets, and Slides. After a one-time browser login, scripts can list files, create Docs and Sheets, and change their contents.

---

## Repository structure

The library lives at the repo root. `connector_to_google_drive/` holds the scripts that sign in and try the connector.

```
google-drive-plugins/
├── connector.py                 # library: sign-in and file operations
├── example_usage.py             # walkthrough of create and edit
├── create_presentation.py       # builds a Slides deck from a resume
├── requirements.txt             # Python dependencies
├── .env.example                 # template for client id, secret, and paths
└── connector_to_google_drive/
    ├── setup_auth.py            # one-time Google sign-in
    ├── demo.py                  # demo of list, create, and edit
    └── README.md                # setup notes for this folder
```

### `connector.py`

This is the library every other script imports. `GoogleDriveConnector` reads `credentials.json` and `.env`, refreshes `token.json` when the access token expires, and opens a browser login when no valid token exists. After that, the same object lists and searches Drive, uploads files, and creates or edits Docs, Sheets, and Slides.

Running it directly signs in and prints your most recent files:

```bash
python3 connector.py
```

### `connector_to_google_drive/setup_auth.py`

This is the one-time sign-in script for the connector folder. It imports `GoogleDriveConnector` from `connector.py`, opens the browser so you can grant access, and saves `token.json` for later runs. It then lists your 10 most recent Drive files so you can confirm the account connected. Run it once from that folder; `demo.py` and your own scripts reuse the saved token.

```bash
cd connector_to_google_drive
python setup_auth.py
```

---

## Get connected

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create Google OAuth credentials

1. Open [Google Cloud Console](https://console.cloud.google.com).
2. Create a project and enable **Google Drive API**, **Google Docs API**, **Google Sheets API**, and **Google Slides API**.
3. Go to **APIs & Services → Credentials → Create OAuth client ID** and choose **Desktop app**.
4. Download the JSON file, rename it to `credentials.json`, and put it in this folder.
5. While the app is in Testing mode, add your Gmail under **APIs & Services → Google Auth Platform → Audience** as a test user.

### 3. Configure the environment

```bash
cp .env.example .env
```

Fill in `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_ACCOUNT_EMAIL` in `.env`.

### 4. Sign in once

```bash
python3 connector.py
```

Approve access in the browser. The connector saves `token.json` and refreshes it on later runs. A successful run prints your most recent Drive files.

---

## Create and edit files

Import the connector and construct it. The first call authenticates; later calls reuse `token.json`.

```python
from connector import GoogleDriveConnector

conn = GoogleDriveConnector()
```

### Google Docs

Create a Doc, optionally inside a folder and with starting text:

```python
folder = conn.create_folder("Notes")

doc = conn.create_google_doc(
    title="Meeting notes",
    parent_id=folder["id"],
    initial_text="Agenda\n- Review status\n",
)
doc_id = doc["documentId"]
```

Edit an existing Doc by its ID. You can append, find-and-replace, or overwrite the body:

```python
print(conn.read_doc_text(doc_id))

conn.append_to_doc(doc_id, "\nAction items\n- Send the recap\n")
conn.replace_text_in_doc(doc_id, "Review status", "Review launch status")
conn.overwrite_doc(doc_id, "This replaces the whole document.\n")
```

### Google Sheets

Create a spreadsheet and write a range. `write_sheet_range` overwrites the cells you name:

```python
sheet = conn.create_google_sheet(
    title="Scores",
    parent_id=folder["id"],
    sheet_names=["Results"],
)
sheet_id = sheet["spreadsheetId"]

conn.write_sheet_range(
    sheet_id,
    "Results!A1",
    [
        ["Name", "Score"],
        ["Ali", 100],
        ["Sam", 88],
    ],
)
```

Read cells back, add rows, or clear a range:

```python
rows = conn.read_sheet_range(sheet_id, "Results!A1:B10")

conn.append_sheet_rows(sheet_id, "Results!A1", [["Lee", 91]])
conn.clear_sheet_range(sheet_id, "Results!A2:B10")
```

### Files already in Drive

Look up a file, then edit it with the same Doc and Sheet methods. The ID is the long string in the file’s URL.

```python
matches = conn.search_files("Meeting notes")
file_id = matches[0]["id"]

conn.append_to_doc(file_id, "\nFollow-up added later.\n")
```

You can also upload a local file, rename it, or move it into a folder:

```python
uploaded = conn.upload_file("notes.txt", parent_id=folder["id"])
conn.rename_file(uploaded["id"], "notes-2026.txt")
conn.move_file(uploaded["id"], folder["id"])
```

A full walkthrough of these calls is in `example_usage.py`:

```bash
python3 example_usage.py
```

---

## Files

| File | Purpose |
|------|---------|
| `connector.py` | Library for sign-in and Drive, Docs, Sheets, and Slides operations |
| `connector_to_google_drive/setup_auth.py` | One-time browser login that saves `token.json` and lists recent files |
| `connector_to_google_drive/demo.py` | Demo that lists files, then creates and edits a Doc and a Sheet |
| `example_usage.py` | Live walkthrough: connect, create a folder, then create and edit a Doc and a Sheet |
| `create_presentation.py` | Builds a portfolio presentation from a resume |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment template (copy to `.env`; do not commit `.env`) |

---

## Security

Do not commit secrets. `.gitignore` excludes `.env`, `credentials.json`, and `token.json`.

To revoke access, open [Google Account permissions](https://myaccount.google.com/permissions) and remove the app.
