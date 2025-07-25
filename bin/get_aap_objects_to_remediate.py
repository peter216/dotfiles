#!/usr/bin/env python
"""
This script retrieves objects from Ansible Automation Platform (AAP) using the AAP API.
It checks if the objects are associated with any organization and saves the results to an HTML file.
"""

import pandas as pd
import requests
import os

requests.packages.urllib3.disable_warnings()

bearer_token = os.getenv("BEARER_TOKEN")

base_url = "https://mind-aap.marriott.com/api/v2/"


def get_aap_objects(object_type):
    payload = {}
    headers = {"Authorization": "Bearer " + bearer_token}
    done = False
    page = 1
    json_results = []
    while not done:
        url = f"{base_url}{object_type}?page_size=200&page={page}"
        response = requests.get(url, headers=headers, data=payload, verify=False)
        assert response.status_code == 200, (
            f"Failed to get {object_type}: {response.content}"
        )
        json_data = response.json()
        next = json_data["next"]
        if next is None:
            done = True
        json_results.extend(json_data["results"])
        page += 1
    return json_results


objects = [
    "job_templates",
    "workflow_job_templates",
    "projects",
    "inventories",
    "credentials",
]
columns1 = ["id", "name", "description", "last_job_run", "organization"]
columns2 = ["id", "name", "description", "organization"]
with open("aap_objects.html", "w") as f:
    f.write("<html><head><title>AAP Objects</title></head><body>")
    f.write("<h1>AAP Objects not in any Organization</h1>")
for object in objects:
    if object in ["inventories", "credentials"]:
        columns = columns2
    else:
        columns = columns1
    json_results = get_aap_objects(object)
    df = pd.DataFrame(json_results, dtype=str)
    df.fillna("0", inplace=True)
    fdf = df[df["organization"] == "0"]
    print(f"object: {object}")
    print(df.organization.value_counts())
    print()
    if len(fdf) > 0:
        with open("aap_objects.html", "a") as f:
            f.write(f"<h2>{object}</h2>")
            f.write(fdf.to_html(columns=columns, index=False))
        print(f"Saved {object} to aap_objects.html")
    else:
        print(f"No {object} meets the criteria")
    print()
with open("aap_objects.html", "a") as f:
    f.write("</body></html>")
