#!/usr/bin/env python

## Import necessary libraries
import os
import json
import requests
import sys
from datetime import datetime

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

## Configuration
API_KEY = os.environ.get("POSTMAN_API_KEY")
OUTPUT_DIR = "postman_exports"
BASE_URL = "https://api.getpostman.com"

## Function to create output directory
def create_output_directory():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"{OUTPUT_DIR}_{timestamp}"
    os.makedirs(dir_name, exist_ok=True)
    return dir_name

## Function to get all workspaces
def get_workspaces():
    headers = {
        "X-Api-Key": API_KEY
    }
    response = requests.get(f"{BASE_URL}/workspaces", headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["workspaces"]

## Function to get collections in a workspace
def get_collections(workspace_id):
    headers = {
        "X-Api-Key": API_KEY
    }
    response = requests.get(f"{BASE_URL}/collections?workspace={workspace_id}", headers=headers, verify=False)
    response.raise_for_status()
    return response.json()["collections"]

## Function to export a collection in v2.1 format
def export_collection(collection_id, collection_name, workspace_name, output_dir):
    headers = {
        "X-Api-Key": API_KEY
    }
    # The 'collection' query parameter allows downloading in Collection v2.1 format
    response = requests.get(f"{BASE_URL}/collections/{collection_id}", headers=headers, params={"collection": "v2.1"}, verify=False)
    response.raise_for_status()

    # Create a valid filename
    safe_collection_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in collection_name)
    safe_workspace_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in workspace_name)

    # Create workspace subdirectory
    workspace_dir = os.path.join(output_dir, safe_workspace_name)
    os.makedirs(workspace_dir, exist_ok=True)

    # Write the collection file
    file_path = os.path.join(workspace_dir, f"{safe_collection_name}.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(response.json(), f, indent=2)

    return file_path

## Main function
def main():
    ## Check if API key is set
    if not API_KEY:
        print("Error: POSTMAN_API_KEY environment variable not set")
        print("Please set your Postman API key with: export POSTMAN_API_KEY='your-api-key'")
        sys.exit(1)

    output_dir = create_output_directory()
    print(f"Exporting collections to {output_dir}...")

    ## Get all workspaces
    print("Getting workspaces...")
    try:
        workspaces = get_workspaces()
    except requests.exceptions.RequestException as e:
        print(f"Error getting workspaces: {e}")
        sys.exit(1)

    print(f"Found {len(workspaces)} workspaces")

    ## Process each workspace
    total_collections = 0
    for workspace in workspaces:
        workspace_id = workspace["id"]
        workspace_name = workspace["name"]
        print(f"\nProcessing workspace: {workspace_name}")

        try:
            ## Get collections in the workspace
            collections = get_collections(workspace_id)
            print(f"Found {len(collections)} collections in workspace '{workspace_name}'")

            ## Export each collection
            for collection in collections:
                collection_id = collection["uid"]
                collection_name = collection["name"]
                try:
                    file_path = export_collection(collection_id, collection_name, workspace_name, output_dir)
                    print(f"  - Exported: {collection_name} -> {file_path}")
                    total_collections += 1
                except requests.exceptions.RequestException as e:
                    print(f"  - Error exporting collection '{collection_name}': {e}")

        except requests.exceptions.RequestException as e:
            print(f"Error getting collections for workspace '{workspace_name}': {e}")

    print(f"\nExport complete! Exported {total_collections} collections from {len(workspaces)} workspaces to {output_dir}")

## Execute main function when script is run directly
if __name__ == "__main__":
    main()
