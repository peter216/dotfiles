from __future__ import print_function
import json
import subprocess
import argparse
import socket
import webbrowser
from urllib.parse import urlparse, parse_qs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
#from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# gopass paths - adjust if needed
GOPASS_CREDENTIALS_PATH = "email/gmail/credentials.json"
GOPASS_TOKEN_PATH = "email/gmail/token.json"

def gopass_cat(entry):
    """Retrieve secret from gopass."""
    result = subprocess.run(
        ["gopass", "cat", entry],
        #["gopass", "show", "-o", entry],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def load_json_from_gopass(entry):
    """Load JSON from gopass."""
    return json.loads(gopass_cat(entry))

def save_json_to_gopass(entry, data):
    """Save JSON to gopass."""
    json_str = json.dumps(data, indent=2)
    subprocess.run(
        ["gopass", "insert", "-f", entry],
        input=json_str,
        text=True,
        check=True
    )

def run_local_server(flow, host='localhost', port=0, timeout=60):
    """Start local HTTP server to handle OAuth redirect."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)
        redirect_port = s.getsockname()[1]
        flow.redirect_uri = f"http://{host}:{redirect_port}/"
        auth_url, _ = flow.authorization_url(prompt='consent')

        print(f"Opening browser for auth, listening on http://{host}:{redirect_port}/ ...")
        webbrowser.open(auth_url)

        s.settimeout(timeout)
        try:
            conn, _ = s.accept()
        except socket.timeout:
            print("Timeout waiting for OAuth callback.")
            return None

        with conn:
            request = conn.recv(1024).decode()
            path = request.split(" ")[1]
            params = parse_qs(urlparse(path).query)
            code = params.get("code", [None])[0]
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nAuth complete. You can close this tab.")
            return code

def manual_auth(flow):
    """Manual OAuth flow for headless use."""
    auth_url, _ = flow.authorization_url(prompt='consent')
    print("Go to this URL in your browser:\n")
    print(auth_url)
    code = input("\nEnter the authorization code here: ").strip()
    flow.fetch_token(code=code)
    return flow.credentials

def get_service(headless=False):
    creds = None
    try:
        token_data = load_json_from_gopass(GOPASS_TOKEN_PATH)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    except subprocess.CalledProcessError:
        pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_json_to_gopass(GOPASS_TOKEN_PATH, json.loads(creds.to_json()))
        else:
            creds_json = load_json_from_gopass(GOPASS_CREDENTIALS_PATH)
            #flow = Flow.from_client_config(creds_json, SCOPES)
            flow = InstalledAppFlow.from_client_config(
                creds_json, SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')

            if headless:
                creds = manual_auth(flow)
            else:
                code = run_local_server(flow)
                if code:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                else:
                    print("Falling back to manual auth.")
                    creds = manual_auth(flow)

            save_json_to_gopass(GOPASS_TOKEN_PATH, json.loads(creds.to_json()))

    return build('gmail', 'v1', credentials=creds)

def search_messages(service, query):
    """Search for messages matching query and return their IDs."""
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    return [m['id'] for m in messages]

def get_list_unsubscribe(service, msg_id):
    """Fetch the List-Unsubscribe header from a message."""
    msg = service.users().messages().get(
        userId='me',
        id=msg_id,
        format='metadata',
        metadataHeaders=['List-Unsubscribe']
    ).execute()
    headers = msg.get('payload', {}).get('headers', [])
    for header in headers:
        if header['name'].lower() == 'list-unsubscribe':
            return header['value']
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gmail unsubscribe scanner")
    parser.add_argument('--headless', action='store_true', help="Use manual auth instead of local server")
    args = parser.parse_args()

    service = get_service(headless=args.headless)
    query = "has:unsubscribe"
    msg_ids = search_messages(service, query)

    print(f"Found {len(msg_ids)} messages with unsubscribe links.")
    for msg_id in msg_ids:
        unsub = get_list_unsubscribe(service, msg_id)
        if unsub:
            print(f"{msg_id}: {unsub}")
