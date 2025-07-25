#!/usr/bin/env python
"""
This script updates the organization of job templates in Ansible Automation Platform (AAP) using the AAP API.
It takes a list of template IDs as input and updates their organization to a specified organization ID.
"""

import requests
import os
import argparse

# Disable SSL warnings (not recommended for production code)
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)
# Set up argument parser
parser = argparse.ArgumentParser(description="Update job templates in AAP")
parser.add_argument(
    "--template_ids",
    nargs="+",
    type=int,
    required=True,
    help="List of template IDs to update",
)
args = parser.parse_args()

template_ids = args.template_ids

# Replace with your actual values
bearer_token = os.getenv("BEARER_TOKEN")
base_url = "https://mind-aap.marriott.com/api/v2"
organization_id = 1
# template_ids = [694, 696, 1312, 697, 698, 1313]  # List of template IDs to update

headers = {
    "Authorization": f"Bearer {bearer_token}",
    "Content-Type": "application/json",
}

for template_id in template_ids:
    url = f"{base_url}/job_templates/{template_id}/"
    data = {"organization": organization_id}
    response = requests.patch(url, headers=headers, json=data, verify=False)
    if response.status_code == 200:
        print(f"Successfully updated template {template_id}")
    else:
        print(f"Failed to update template {template_id}: {response.content}")
