#!/usr/bin/env python3

import csv
import json
import logging
import os
import subprocess
import sys
import shutil
from datetime import datetime

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

if os.getenv("DEBUG"):
    LOGLEVEL = logging.DEBUG
else:
    LOGLEVEL = logging.INFO

logging.basicConfig(
    level=LOGLEVEL,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("aap_leak_check.log"), logging.StreamHandler()],
)

HOME = os.path.expanduser("~")
NOW = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

# Configuration
if (ansible_api_token := os.getenv("AAP_DEV_RW_TOKEN")) is None:
    logging.error("Environment variable AAP_DEV_RW_TOKEN is not set.")
    sys.exit(1)
ansible_api_url = "https://mihdqdevc01.marriott.com/api/v2/jobs/"
output_folder = f"{HOME}/sandbox/aap_job_outputs/data"
trufflehog_log = f"{HOME}/sandbox/aap_job_outputs/trufflehog.log"
trufflehog_out = f"{HOME}/sandbox/aap_job_outputs/trufflehog_output.json"
trufflehog_err = f"{HOME}/sandbox/aap_job_outputs/trufflehog_error.txt"
csv_output = f"{HOME}/sandbox/aap_job_outputs/security_concerns.csv"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# If files exist, move them to an archive folder
archive_folder = f"{HOME}/sandbox/aap_job_outputs/archive"
os.makedirs(archive_folder, exist_ok=True)
for file in [
    trufflehog_out,
    trufflehog_err,
    csv_output,
    "aap_leak_check.log",
]:
    if os.path.exists(file):
        date_filename = f"{"".join(file.split('.')[0:-1])}_{NOW}.{file.split('.')[-1]}"
        shutil.move(file, os.path.join(archive_folder, date_filename))
        logging.info(f"Moved {file} to archive folder.")

# Function to download job stdout
def download_job_stdout(job_data):
    job_id = job_data.get("id")
    if not job_id:
        logging.error(f"Job ID is missing for job data: {job_data}")
        return
    logging.info(f"Processing job {job_id} - {job_data['name']} started at {job_data['started']}")
    if os.path.exists(
        os.path.join(output_folder, f"job_{job_id}.txt")
    ):
        logging.info(f"Job {job_id} stdout already exists, skipping download.")
        return
    logging.info(f"Downloading stdout for job {job_id}")
    url = f"{ansible_api_url}{job_id}/stdout/?format=txt_download"
    headers = {
        "Authorization": f"Bearer {ansible_api_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        outputfilepath = os.path.join(output_folder, f"job_{job_id}.txt")
        with open(outputfilepath, "w") as file:
            file.write(response.text)
        logging.info(
            f"Downloaded stdout for job {job_id} and wrote to {outputfilepath}"
        )
    else:
        logging.error(f"Failed to download stdout for job {job_id}")
        logging.error(f"Response: {response.text}")
        logging.error(f"Status code: {response.status_code}")
        sys.exit(1)


# Function to run TruffleHog
def run_trufflehog():
    results = subprocess.run(
        [
            "trufflehog",
            "--json",
            "--no-update",
            "filesystem",
            output_folder,
        ],
        capture_output=True,
    )
    if results.returncode != 0:
        logging.error(f"TruffleHog failed with return code {results.returncode}")
        with open(trufflehog_err, "w") as err_file:
            err_file.write(results.stderr.decode("utf-8"))
        logging.error(f"TruffleHog stderr written to {trufflehog_err}.")
        sys.exit(1)
    if results.stdout:
        with open(trufflehog_out, "w") as file:
            json.dump(
                json.loads(results.stdout.decode("utf-8")), file, indent=4
            )
        logging.info(f"TruffleHog results saved to {trufflehog_out}")
    else:
        logging.warning("TruffleHog did not produce any output.")
    if results.stderr:
        with open(trufflehog_log, "w") as log_file:
            log_file.write(results.stderr.decode("utf-8"))
        logging.warning(f"TruffleHog stderr written to {trufflehog_log}.")


# Function to create CSV from TruffleHog output
def create_csv():
    try:
        with open(trufflehog_out, "r") as file:
            trufflehog_results = json.load(file)
    except FileNotFoundError:
        logging.warning("TruffleHog output file not found")
        sys.exit(0)

    with open(csv_output, "w", newline="") as csvfile:
        fieldnames = ["job_id", "message"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for result in trufflehog_results:
            job_id = result["path"].split("_")[1].split(".")[0]
            message = result["message"]
            writer.writerow({"job_id": job_id, "message": message})
    logging.info(f"Security concerns have been saved to {csv_output}")


def get_filtered_jobs(api_url, api_token):
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    params = {"page_size": 100}
    jobs = []
    page = 1

    while True:
        logging.info(f"Getting jobs from page {page}")
        try:
            response = requests.get(
                f"{api_url}?page={page}",
                headers=headers,
                params=params,
                verify=False,
            )
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting job: {e.__class__.__name__} - {e}")
            sys.exit(1)

        data = response.json()

        if "results" not in data or not data["results"]:
            break

        if page == 3:
            break

        for job in data["results"]:
            jobs.append(
                {"id": job["id"], "name": job["name"], "started": job["started"]}
            )

        page += 1
    logging.info(f"Total jobs: {len(jobs)}")
    return jobs


# Main script
job_data_objects = get_filtered_jobs(ansible_api_url, ansible_api_token)
for job_data in job_data_objects:
    download_job_stdout(job_data)

run_trufflehog()
create_csv()

print(f"Security concerns have been saved to {csv_output}")
