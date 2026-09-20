# Google Drive Plugins

A robust Python connector for **Google Drive**, **Google Docs**, **Google Sheets**, and **Google Slides**.

---

## Files

| File | Purpose |
|------|---------|
| `connector.py` | Main connector class — Drive / Docs / Sheets / Slides auth & operations |
| `create_presentation.py` | Builds a 5-slide portfolio presentation from a resume |
| `example_usage.py` | Full walkthrough demo of every feature |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template (copy → `.env`, never commit) |

---

## Setup (5 minutes)

### 1 — Install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2 — Get Google OAuth2 credentials
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → enable **Drive API**, **Docs API**, **Sheets API**, **Slides API**
3. APIs & Services → Credentials → **Create OAuth client ID** → Desktop app
4. Download JSON → rename to `credentials.json` → place in this folder
5. Add your Gmail to test users: APIs & Services → Google Auth Platform → Audience

### 3 — Configure environment
```bash
cp .env.example .env
# Edit .env and fill in GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
```

### 4 — Authenticate (one-time browser login)
```bash
python3 connector.py
```

After approving in the browser, `token.json` is saved and auto-refreshes forever.

---

## Quick start

```python
from connector import GoogleDriveConnector

conn = GoogleDriveConnector()

# List files
for f in conn.list_files(max_results=10):
    print(f["name"])

# Create a Google Doc
doc = conn.create_google_doc("My Doc", initial_text="Hello!\n")

# Create a Google Sheet and write data
sheet = conn.create_google_sheet("My Sheet")
conn.write_sheet_range(sheet["spreadsheetId"], "Sheet1!A1", [["Name", "Score"], ["Ali", 100]])
```

---

## Security

> ⚠️ **Never commit secrets.** The following are in `.gitignore`:
> - `.env`
> - `credentials.json`
> - `token.json`

---

## API reference

See `connector.py` docstrings — covers Drive, Docs, Sheets with full method signatures.
