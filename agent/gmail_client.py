import base64, os, re, datetime as dt
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from shared.config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _creds():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of this file
    # Use shared configuration or fallback to local paths
    cred_path = GMAIL_CREDENTIALS_PATH or os.path.join(base_dir, "credentials.json")
    token_path = GMAIL_TOKEN_PATH or os.path.join(base_dir, "token.json")

    creds = None
    # Check if we have a saved token first
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # google-authed client refreshes automatically when used
            pass
        else:
            # Need to authenticate with credentials.json
            if not os.path.exists(cred_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {cred_path}. "
                    "Please download it from Google Cloud Console and place it in the agent directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)

            # Try local server first (requires proper OAuth redirect URIs setup)
            ports_to_try = [8080, 49256, 8000]
            creds = None

            for port in ports_to_try:
                try:
                    print(f"Attempting to start OAuth server on port {port}...")
                    creds = flow.run_local_server(port=port, open_browser=True)
                    print(f"✓ Successfully authenticated on port {port}")
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "OAuth 2.0" in error_msg or "redirect_uri" in error_msg:
                        # OAuth policy error - redirect URI not configured
                        print(f"✗ Port {port} failed due to OAuth configuration issue")
                        print(f"  Error: {error_msg[:100]}")
                    else:
                        # Port in use or other error
                        print(f"✗ Port {port} unavailable: {error_msg[:50]}")
                    continue

            # If local server failed, fall back to console-based auth
            if not creds:
                print("\n" + "=" * 70)
                print("⚠ Could not use local server authentication.")
                print("Switching to manual authentication mode...")
                print("=" * 70)
                print("\n1. A browser window will open (or copy the URL that appears)")
                print("2. Sign in and authorize the app")
                print("3. You may see 'redirect_uri_mismatch' - that's OK!")
                print("4. Copy the code from the URL bar or the page")
                print("5. Paste it below\n")

                creds = flow.run_console()

            # Save the credentials for next time
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            print(f"✓ Credentials saved to {token_path}")
    return creds


def _svc():
    return build("gmail", "v1", credentials=_creds(), cache_discovery=False)


def list_messages(
    query: str = "",
    max_results: int = 20,
    newer_than_days: Optional[int] = None,
    label_ids: Optional[List[str]] = None,
) -> List[Dict]:
    svc = _svc()
    q = query or ""
    if newer_than_days:
        q = (q + f" newer_than:{newer_than_days}d").strip()
    resp = (
        svc.users()
        .messages()
        .list(userId="me", q=q, maxResults=max_results, labelIds=label_ids or None)
        .execute()
    )
    return resp.get("messages", [])


def get_message(message_id: str) -> Dict:
    svc = _svc()
    return (
        svc.users().messages().get(userId="me", id=message_id, format="full").execute()
    )


def _decode_part(body) -> str:
    data = body.get("data")
    if not data:
        return ""
    return base64.urlsafe_b64decode(data.encode("utf-8")).decode(errors="ignore")


def _clean_html(html: str) -> str:
    """Clean HTML by removing styles, scripts, and extra whitespace."""
    if not html:
        return ""

    # Remove style blocks and their content
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove script blocks and their content
    html = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    # Remove HTML comments
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # Remove all HTML tags
    html = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    html = (
        html.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
    )
    # Collapse multiple spaces/newlines
    html = re.sub(r"\s+", " ", html)
    # Strip leading/trailing whitespace
    return html.strip()


def extract_text(payload: Dict) -> str:
    """Return best-effort plain text from MIME payload."""
    if not payload:
        return ""
    mime = payload.get("mimeType", "")
    body = payload.get("body", {})
    parts = payload.get("parts", [])

    # If single-part
    if not parts:
        if "text/plain" in mime:
            return _decode_part(body)
        if "text/html" in mime:
            html = _decode_part(body)
            return _clean_html(html)
        return ""

    # Multipart: prefer plain, fallback html
    text_chunks = []
    html_chunks = []
    stack = [payload]
    while stack:
        p = stack.pop()
        if p.get("parts"):
            stack.extend(p["parts"])
            continue
        mt = p.get("mimeType", "")
        b = p.get("body", {})
        if "text/plain" in mt:
            text_chunks.append(_decode_part(b))
        elif "text/html" in mt:
            html_chunks.append(_decode_part(b))

    if text_chunks:
        return "\n".join(text_chunks)
    if html_chunks:
        return _clean_html("\n".join(html_chunks))
    return ""


def message_summary(msg: Dict) -> Dict:
    headers = {
        h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])
    }
    snippet = msg.get("snippet", "")
    text = extract_text(msg.get("payload", {}))
    return {
        "id": msg["id"],
        "threadId": msg.get("threadId"),
        "from": headers.get("from"),
        "to": headers.get("to"),
        "subject": headers.get("subject"),
        "date": headers.get("date"),
        "snippet": snippet,
        "text": text[:50000],  # guardrails
    }
