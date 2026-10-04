# Google Drive Connector

A robust Python connector for Google Drive, Docs, and Sheets using OAuth 2.0.

---

## ⚡ Quick Start

### Step 1 — Install dependencies

```bash
cd connector_to_google_drive
pip install -r requirements.txt
```

---

### Step 2 — Set up Google Cloud credentials

> **Why?** Google Drive API requires OAuth credentials from Google Cloud Console.
> Your Google account password is never used or stored.

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)** and sign in with `ali.naeim.gdrive@gmail.com`.

2. **Create a project** (or select an existing one).

3. Enable these three APIs (search each one):
   - **Google Drive API**
   - **Google Docs API**
   - **Google Sheets API**

4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Name: anything (e.g. "Drive Connector")

5. Download the JSON file → **rename it to `credentials.json`** → place it in this folder.

   *OR* copy the Client ID and Client Secret values and paste them into `.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

6. In **APIs & Services → OAuth consent screen**:
   - Add `ali.naeim.gdrive@gmail.com` as a **Test user** (while the app is in "Testing" mode).

---

### Step 3 — Authenticate (once)

```bash
python setup_auth.py
```

A browser window will open. Sign in with your Google account and click **Allow**.
A `token.json` file is saved — future runs are silent (no browser).

---

### Step 4 — Run the demo

```bash
python demo.py
```

---

## 📖 API Reference

```python
from connector import GoogleDriveConnector

conn = GoogleDriveConnector()
conn.connect()
```

### Drive

| Method | Description |
|--------|-------------|
| `list_files(query, page_size)` | List / search files |
| `search_files(name, mime_type)` | Search by name |
| `get_file_metadata(file_id)` | Full metadata for one file |
| `create_folder(name, parent_id)` | Create a folder |
| `upload_file(local_path, ...)` | Upload a local file |
| `delete_file(file_id)` | Permanently delete a file |

### Google Docs

| Method | Description |
|--------|-------------|
| `create_doc(title, parent_id)` | Create a new Doc |
| `read_doc(doc_id)` | Raw document resource |
| `get_doc_text(doc_id)` | Plain text content |
| `append_to_doc(doc_id, text)` | Append text at end |
| `replace_doc_text(doc_id, find, replace)` | Find & replace |

### Google Sheets

| Method | Description |
|--------|-------------|
| `create_sheet(title, parent_id)` | Create a new Spreadsheet |
| `read_sheet(sheet_id, range_)` | Read cell range (2-D list) |
| `write_sheet(sheet_id, range_, values)` | Write to a range |
| `append_to_sheet(sheet_id, range_, values)` | Append rows |
| `clear_sheet_range(sheet_id, range_)` | Clear a range |

---

## 🔒 Security

- `token.json` and `credentials.json` are in `.gitignore` — never committed.
- Your Google account **password is never used** by this connector.
- To revoke access: visit [myaccount.google.com/permissions](https://myaccount.google.com/permissions) and remove the app.
