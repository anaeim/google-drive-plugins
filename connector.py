"""
connector.py — Google Drive Connector
======================================
A robust, reusable connector for the Google Drive, Docs, and Sheets APIs.

Features
--------
- OAuth2 authentication with automatic token refresh
- List / search files and folders
- Upload, download, and delete files
- Create and edit Google Docs (read body, append/replace text)
- Create and edit Google Sheets (read, write, append rows)
- Proper logging and error handling throughout
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ── Environment ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
load_dotenv(_HERE / ".env")

# ── Logging ────────────────────────────────────────────────────────────────────
_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("gdrive_connector")

# ── OAuth2 scopes ──────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/drive",           # full Drive access
    "https://www.googleapis.com/auth/documents",        # Docs read/write
    "https://www.googleapis.com/auth/spreadsheets",     # Sheets read/write
    "https://www.googleapis.com/auth/presentations",    # Slides read/write
]

# MIME-type constants
MIME_FOLDER   = "application/vnd.google-apps.folder"
MIME_DOC      = "application/vnd.google-apps.document"
MIME_SHEET    = "application/vnd.google-apps.spreadsheet"
MIME_SLIDE    = "application/vnd.google-apps.presentation"


# ═══════════════════════════════════════════════════════════════════════════════
#  Auth
# ═══════════════════════════════════════════════════════════════════════════════

def _load_credentials(credentials_file: Path, token_file: Path) -> Credentials:
    """Load OAuth2 credentials, refreshing or re-authorising as needed."""
    creds: Optional[Credentials] = None

    # Try loading a saved token first
    if token_file.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            logger.debug("Loaded saved token from %s", token_file)
        except Exception as exc:
            logger.warning("Could not load token file (%s), will re-authenticate.", exc)
            creds = None

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            logger.info("Access token refreshed successfully.")
        except RefreshError:
            logger.warning("Token refresh failed — starting fresh OAuth2 flow.")
            creds = None

    # Run browser-based OAuth2 flow if no valid creds
    if not creds or not creds.valid:
        if not credentials_file.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {credentials_file}.\n"
                "Download it from https://console.cloud.google.com/ → "
                "APIs & Services → Credentials → OAuth 2.0 Client IDs."
            )
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_file), SCOPES
        )
        creds = flow.run_local_server(port=0, prompt="consent")
        logger.info("OAuth2 flow completed. Token saved to %s", token_file)

    # Persist the (possibly refreshed) token
    token_file.write_text(creds.to_json())
    return creds


# ═══════════════════════════════════════════════════════════════════════════════
#  Main connector class
# ═══════════════════════════════════════════════════════════════════════════════

class GoogleDriveConnector:
    """
    High-level connector for Google Drive, Docs, and Sheets.

    Usage
    -----
    >>> conn = GoogleDriveConnector()          # authenticates on first run
    >>> files = conn.list_files()
    >>> for f in files:
    ...     print(f["name"], f["id"])
    """

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
    ) -> None:
        _creds_path = Path(credentials_file or os.getenv("CREDENTIALS_FILE", "credentials.json"))
        _token_path = Path(token_file       or os.getenv("TOKEN_FILE",       "token.json"))

        # Resolve relative paths relative to this file's directory
        if not _creds_path.is_absolute():
            _creds_path = _HERE / _creds_path
        if not _token_path.is_absolute():
            _token_path = _HERE / _token_path

        logger.info("Authenticating with Google APIs…")
        self._creds = _load_credentials(_creds_path, _token_path)

        self._drive   = build("drive",        "v3", credentials=self._creds)
        self._docs    = build("docs",          "v1", credentials=self._creds)
        self._sheets  = build("sheets",        "v4", credentials=self._creds)
        logger.info("Connected successfully as %s", os.getenv("GOOGLE_ACCOUNT_EMAIL", "unknown"))

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _safe_call(self, request) -> Any:
        """Execute a Google API request and surface errors cleanly."""
        try:
            return request.execute()
        except HttpError as exc:
            logger.error("Google API error %s: %s", exc.resp.status, exc.error_details)
            raise

    # ══════════════════════════════════════════════════════════════════════════
    #  DRIVE — File / Folder operations
    # ══════════════════════════════════════════════════════════════════════════

    def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        max_results: int = 100,
        order_by: str = "modifiedTime desc",
        include_trashed: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List files in Google Drive.

        Parameters
        ----------
        folder_id : str, optional
            Restrict listing to a specific folder (Drive folder ID).
        query : str, optional
            Additional Drive query string, e.g. ``"mimeType='application/pdf'"``
        max_results : int
            Maximum number of items to return (default 100).
        order_by : str
            Sort order (default: newest first).
        include_trashed : bool
            Include trashed files (default False).

        Returns
        -------
        list of dict with keys: id, name, mimeType, modifiedTime, size, parents
        """
        parts = []
        if not include_trashed:
            parts.append("trashed = false")
        if folder_id:
            parts.append(f"'{folder_id}' in parents")
        if query:
            parts.append(query)

        q = " and ".join(parts) if parts else None
        fields = "nextPageToken, files(id, name, mimeType, modifiedTime, size, parents, webViewLink)"

        all_files: List[Dict] = []
        page_token = None

        while True:
            kwargs: Dict[str, Any] = dict(
                pageSize=min(max_results - len(all_files), 1000),
                fields=fields,
                orderBy=order_by,
            )
            if q:
                kwargs["q"] = q
            if page_token:
                kwargs["pageToken"] = page_token

            result = self._safe_call(self._drive.files().list(**kwargs))
            all_files.extend(result.get("files", []))
            page_token = result.get("nextPageToken")

            if not page_token or len(all_files) >= max_results:
                break

        logger.info("Listed %d file(s).", len(all_files))
        return all_files[:max_results]

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Return full metadata for a single file."""
        result = self._safe_call(
            self._drive.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, size, parents, webViewLink, description",
            )
        )
        return result

    def search_files(self, name_contains: str, **kwargs) -> List[Dict[str, Any]]:
        """Convenience wrapper: search by name substring."""
        return self.list_files(query=f"name contains '{name_contains}'", **kwargs)

    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a folder in Drive. Returns the new folder metadata."""
        meta: Dict[str, Any] = {"name": name, "mimeType": MIME_FOLDER}
        if parent_id:
            meta["parents"] = [parent_id]
        result = self._safe_call(self._drive.files().create(body=meta, fields="id, name, webViewLink"))
        logger.info("Created folder '%s' (id=%s)", name, result["id"])
        return result

    def upload_file(
        self,
        local_path: str,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload a local file to Google Drive.

        Parameters
        ----------
        local_path : str  — path to the local file
        name : str, optional  — Drive file name (defaults to filename)
        parent_id : str, optional  — destination folder ID
        mime_type : str, optional  — MIME type (auto-detected if omitted)

        Returns
        -------
        dict with id, name, webViewLink
        """
        local = Path(local_path)
        if not local.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        meta: Dict[str, Any] = {"name": name or local.name}
        if parent_id:
            meta["parents"] = [parent_id]

        media = MediaFileUpload(str(local), mimetype=mime_type, resumable=True)
        result = self._safe_call(
            self._drive.files().create(body=meta, media_body=media, fields="id, name, webViewLink")
        )
        logger.info("Uploaded '%s' → Drive id=%s", local.name, result["id"])
        return result

    def download_file(self, file_id: str, destination: str) -> Path:
        """
        Download a binary Drive file to disk.
        For Google Docs/Sheets use ``export_file`` instead.
        """
        dest = Path(destination)
        request = self._drive.files().get_media(fileId=file_id)
        with io.FileIO(str(dest), "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        logger.info("Downloaded file %s → %s", file_id, dest)
        return dest

    def export_file(
        self,
        file_id: str,
        destination: str,
        mime_type: str = "application/pdf",
    ) -> Path:
        """
        Export a Google Workspace file (Doc/Sheet/Slide) to a chosen format.

        Common mime_type values
        -----------------------
        - "application/pdf"
        - "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  (docx)
        - "text/plain"
        - "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"        (xlsx)
        - "text/csv"
        """
        dest = Path(destination)
        request = self._drive.files().export_media(fileId=file_id, mimeType=mime_type)
        with io.FileIO(str(dest), "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        logger.info("Exported file %s as %s → %s", file_id, mime_type, dest)
        return dest

    def delete_file(self, file_id: str) -> None:
        """Permanently delete a file from Drive."""
        self._safe_call(self._drive.files().delete(fileId=file_id))
        logger.info("Deleted file %s", file_id)

    def move_file(self, file_id: str, new_parent_id: str) -> Dict[str, Any]:
        """Move a file to a different folder."""
        meta = self._safe_call(
            self._drive.files().get(fileId=file_id, fields="parents")
        )
        old_parents = ",".join(meta.get("parents", []))
        result = self._safe_call(
            self._drive.files().update(
                fileId=file_id,
                addParents=new_parent_id,
                removeParents=old_parents,
                fields="id, name, parents",
            )
        )
        logger.info("Moved file %s → folder %s", file_id, new_parent_id)
        return result

    def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a file or folder."""
        result = self._safe_call(
            self._drive.files().update(
                fileId=file_id, body={"name": new_name}, fields="id, name"
            )
        )
        logger.info("Renamed file %s → '%s'", file_id, new_name)
        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  GOOGLE DOCS operations
    # ══════════════════════════════════════════════════════════════════════════

    def create_google_doc(
        self,
        title: str,
        parent_id: Optional[str] = None,
        initial_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Google Doc.

        Parameters
        ----------
        title : str  — document title
        parent_id : str, optional  — folder to place it in
        initial_text : str, optional  — text to insert after creation

        Returns
        -------
        dict with documentId, title, revisionId
        """
        # Create the Doc via Drive (so we can set a parent folder)
        meta: Dict[str, Any] = {"name": title, "mimeType": MIME_DOC}
        if parent_id:
            meta["parents"] = [parent_id]
        drive_result = self._safe_call(
            self._drive.files().create(body=meta, fields="id, name, webViewLink")
        )
        doc_id = drive_result["id"]
        logger.info("Created Google Doc '%s' (id=%s)", title, doc_id)

        if initial_text:
            self.append_to_doc(doc_id, initial_text)

        return self.get_doc(doc_id)

    def get_doc(self, document_id: str) -> Dict[str, Any]:
        """Return the full document resource for a Google Doc."""
        return self._safe_call(self._docs.documents().get(documentId=document_id))

    def read_doc_text(self, document_id: str) -> str:
        """Extract all plain text from a Google Doc."""
        doc = self.get_doc(document_id)
        text_parts: List[str] = []
        for element in doc.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if paragraph:
                for pe in paragraph.get("elements", []):
                    text_run = pe.get("textRun")
                    if text_run:
                        text_parts.append(text_run.get("content", ""))
        return "".join(text_parts)

    def append_to_doc(self, document_id: str, text: str) -> Dict[str, Any]:
        """Append text to the end of a Google Doc."""
        doc = self.get_doc(document_id)
        # End of document index (subtract 1 for the trailing newline sentinel)
        end_index = doc["body"]["content"][-1]["endIndex"] - 1

        requests = [
            {
                "insertText": {
                    "location": {"index": end_index},
                    "text": text,
                }
            }
        ]
        result = self._safe_call(
            self._docs.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            )
        )
        logger.info("Appended %d chars to doc %s", len(text), document_id)
        return result

    def replace_text_in_doc(
        self, document_id: str, find: str, replace: str, match_case: bool = True
    ) -> Dict[str, Any]:
        """Find-and-replace text within a Google Doc."""
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": find, "matchCase": match_case},
                    "replaceText": replace,
                }
            }
        ]
        result = self._safe_call(
            self._docs.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            )
        )
        logger.info("Replaced '%s' with '%s' in doc %s", find, replace, document_id)
        return result

    def clear_doc(self, document_id: str) -> None:
        """Delete all content from a Google Doc, leaving it blank."""
        doc = self.get_doc(document_id)
        content = doc.get("body", {}).get("content", [])
        if len(content) <= 1:
            return  # already empty

        start = content[0].get("endIndex", 1)
        end   = content[-1]["endIndex"] - 1

        if end <= start:
            return

        requests = [{"deleteContentRange": {"range": {"startIndex": start, "endIndex": end}}}]
        self._safe_call(
            self._docs.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            )
        )
        logger.info("Cleared doc %s", document_id)

    def overwrite_doc(self, document_id: str, new_text: str) -> None:
        """Replace all content in a Google Doc with new_text."""
        self.clear_doc(document_id)
        if new_text:
            self.append_to_doc(document_id, new_text)

    # ══════════════════════════════════════════════════════════════════════════
    #  GOOGLE SHEETS operations
    # ══════════════════════════════════════════════════════════════════════════

    def create_google_sheet(
        self,
        title: str,
        parent_id: Optional[str] = None,
        sheet_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new Google Sheet.

        Parameters
        ----------
        title : str  — spreadsheet title
        parent_id : str, optional  — folder to place it in
        sheet_names : list of str, optional  — names for the initial sheets

        Returns
        -------
        Spreadsheet resource dict (includes spreadsheetId, spreadsheetUrl)
        """
        meta: Dict[str, Any] = {"name": title, "mimeType": MIME_SHEET}
        if parent_id:
            meta["parents"] = [parent_id]
        drive_result = self._safe_call(
            self._drive.files().create(body=meta, fields="id, name, webViewLink")
        )
        sheet_id = drive_result["id"]
        logger.info("Created Google Sheet '%s' (id=%s)", title, sheet_id)

        # Rename sheets if requested
        if sheet_names:
            spreadsheet = self.get_sheet(sheet_id)
            existing = spreadsheet.get("sheets", [])
            requests = []
            for i, name in enumerate(sheet_names):
                if i < len(existing):
                    requests.append({
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": existing[i]["properties"]["sheetId"],
                                "title": name,
                            },
                            "fields": "title",
                        }
                    })
                else:
                    requests.append({"addSheet": {"properties": {"title": name}}})
            if requests:
                self._safe_call(
                    self._sheets.spreadsheets().batchUpdate(
                        spreadsheetId=sheet_id, body={"requests": requests}
                    )
                )

        return self.get_sheet(sheet_id)

    def get_sheet(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Return the full spreadsheet resource."""
        return self._safe_call(
            self._sheets.spreadsheets().get(spreadsheetId=spreadsheet_id)
        )

    def read_sheet_range(
        self,
        spreadsheet_id: str,
        range_notation: str = "Sheet1",
        value_render: str = "FORMATTED_VALUE",
    ) -> List[List[Any]]:
        """
        Read values from a sheet range.

        Parameters
        ----------
        spreadsheet_id : str
        range_notation : str  — A1 notation, e.g. "Sheet1!A1:D10" or just "Sheet1"
        value_render : str  — "FORMATTED_VALUE" | "UNFORMATTED_VALUE" | "FORMULA"

        Returns
        -------
        2-D list of cell values (rows × columns)
        """
        result = self._safe_call(
            self._sheets.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueRenderOption=value_render,
            )
        )
        values = result.get("values", [])
        logger.info(
            "Read %d row(s) from %s!%s", len(values), spreadsheet_id, range_notation
        )
        return values

    def write_sheet_range(
        self,
        spreadsheet_id: str,
        range_notation: str,
        values: List[List[Any]],
        value_input: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """
        Write values to a sheet range (overwrites existing data).

        Parameters
        ----------
        spreadsheet_id : str
        range_notation : str  — A1 notation, e.g. "Sheet1!A1"
        values : list of list  — 2-D data (rows × columns)
        value_input : str  — "USER_ENTERED" | "RAW"

        Returns
        -------
        UpdateValuesResponse dict
        """
        body = {"values": values}
        result = self._safe_call(
            self._sheets.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueInputOption=value_input,
                body=body,
            )
        )
        logger.info(
            "Wrote %d row(s) to %s!%s", len(values), spreadsheet_id, range_notation
        )
        return result

    def append_sheet_rows(
        self,
        spreadsheet_id: str,
        range_notation: str,
        rows: List[List[Any]],
        value_input: str = "USER_ENTERED",
    ) -> Dict[str, Any]:
        """
        Append rows after the last non-empty row in the given range.

        Parameters
        ----------
        rows : list of list  — each inner list is one row
        """
        body = {"values": rows}
        result = self._safe_call(
            self._sheets.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_notation,
                valueInputOption=value_input,
                insertDataOption="INSERT_ROWS",
                body=body,
            )
        )
        logger.info(
            "Appended %d row(s) to %s!%s", len(rows), spreadsheet_id, range_notation
        )
        return result

    def clear_sheet_range(
        self, spreadsheet_id: str, range_notation: str
    ) -> Dict[str, Any]:
        """Clear all values in the specified range."""
        result = self._safe_call(
            self._sheets.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id, range=range_notation, body={}
            )
        )
        logger.info("Cleared range %s in %s", range_notation, spreadsheet_id)
        return result

    def add_sheet_tab(self, spreadsheet_id: str, title: str) -> Dict[str, Any]:
        """Add a new sheet (tab) to an existing spreadsheet."""
        requests = [{"addSheet": {"properties": {"title": title}}}]
        result = self._safe_call(
            self._sheets.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": requests}
            )
        )
        logger.info("Added tab '%s' to spreadsheet %s", title, spreadsheet_id)
        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  Utility helpers
    # ══════════════════════════════════════════════════════════════════════════

    def get_or_create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Return the ID of a folder by name, creating it if it doesn't exist."""
        parts = [f"name = '{name}'", f"mimeType = '{MIME_FOLDER}'", "trashed = false"]
        if parent_id:
            parts.append(f"'{parent_id}' in parents")
        results = self._safe_call(
            self._drive.files().list(q=" and ".join(parts), fields="files(id, name)")
        )
        files = results.get("files", [])
        if files:
            logger.debug("Found existing folder '%s' (id=%s)", name, files[0]["id"])
            return files[0]["id"]
        new_folder = self.create_folder(name, parent_id)
        return new_folder["id"]

    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader",
        notify: bool = True,
    ) -> Dict[str, Any]:
        """
        Share a file with another Google account.

        role : "reader" | "commenter" | "writer" | "owner"
        """
        permission = {
            "type": "user",
            "role": role,
            "emailAddress": email,
        }
        result = self._safe_call(
            self._drive.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=notify,
                fields="id, role, type",
            )
        )
        logger.info("Shared file %s with %s as %s", file_id, email, role)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
#  Quick sanity-check when run directly
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    conn = GoogleDriveConnector()
    print("\n=== Files in your Google Drive (most recent 20) ===\n")
    files = conn.list_files(max_results=20)
    if not files:
        print("  (no files found)")
    for f in files:
        size = f.get("size", "—")
        print(f"  [{f['mimeType'].split('.')[-1]:20s}]  {f['name']}  (id={f['id']}  size={size})")
    print(f"\nTotal: {len(files)} file(s)\n")
