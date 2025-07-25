#!/usr/bin/env python3

import requests
import argparse
import os
import platform
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def main(page_id, filepath):
    try:
        nodename = platform.node()
    except Exception as e:
        try:
            nodename = os.uname().nodename
        except Exception as e:
            nodename = "unknown"
    CONFLUENCE_BASIC_AUTH = os.environ["CONFLUENCE_BASIC_AUTH"]

    url = f"https://marriottcloud.atlassian.net/wiki/rest/api/content/{page_id}/child/attachment"

    payload = {'comment': 'Uploaded from Postman'}
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {CONFLUENCE_BASIC_AUTH}',
        'X-Atlassian-Token': 'no-check',
    }
    files = {'file': (os.path.basename(filepath), open(filepath, 'rb'), 'text/csv', {'Expires': '0'})}

    response = requests.put(url, headers=headers, files=files, data=payload, verify=False)

    try:
        assert response.status_code == 200
    except AssertionError:
        print(f"response.status_code: {response.status_code}")
        print(f"response.text: {response.text}")
        print(f"response.headers: {response.headers}")
        print(f"response.request.headers: {response.request.headers}")
        print(f"response.request.body: {response.request.body}")
        raise

    print(f"Successfully uploaded {filepath} to Confluence page {page_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a file to a Confluence page")
    parser.add_argument("page_id", help="The Confluence page ID")
    parser.add_argument("filepath", help="Full path to the file to upload")
    args = parser.parse_args()

    main(args.page_id, args.filepath)
