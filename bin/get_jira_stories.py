#!/usr/bin/env python
"""
Jira Stories Retrieval Tool
===========================

This script retrieves Jira stories for a specific fix version and assignee or team,
then exports the data to a CSV file for further analysis. On Windows, it can
also refresh Excel files with the retrieved data.

Requirements:
-------------
- requests
- pandas
- python-dotenv (optional for env var management)
- xlwings and win32com.client (only required on Windows for Excel features)

Usage:
------
0. To obtain a JIRA API token, use this url: https://id.atlassian.com/manage-profile/security/api-tokens
   (you need to be logged in).
1. Set the JIRA_TOKEN environment variable with your Jira API token.
2. To get your id for the JIRA_ID variable, run the following command:

.. code-block:: bash

    curl -k -u $YOUREMAIL:$JIRA_TOKEN -X GET https://marriottcloud.atlassian.net/rest/api/3/myself 2>/dev/null | jq '.accountId'

3. Run the script with desired options:

.. code-block:: bash

    python get_jira_stories.py [options]

   Available options:
   -d, --debug                Enable debug logging
   -i, --id ID                Jira account ID for the assignee
   -e, --email EMAIL          Jira account email
   -f, --fix-version VERSION  Fix version to filter Jira stories (default: NTWK.25.PI3)
   -o, --output-file FILE     Output CSV file name
   -p, --project-name NAME    Jira project name (default: NTWK)
   -t, --team_name NAME       Search by team name instead of assignee
   --excel-file FILE          Path to Excel file to refresh (Windows only)
   --epics                    Include only epics in the search
   --parse_only               Parse only, do not fetch data from Jira
   --input_file FILE          Input JSON file to parse (for --parse_only)

4. The output will be saved to the specified CSV file (default: ``jira-{FIX_VERSION}.csv``
   or ``jira-{FIX_VERSION}-{TEAM_NAME}.csv`` when using the team name option). The suffix '-epics' will be added to the filename if the --epics option is used.
5. If running on Windows, the script will refresh the specified Excel file with the retrieved data (if specified on the command line or environment).

Examples:
---------
Get stories for a specific assignee:

.. code-block:: bash

    python get_jira_stories.py -i YOUR_JIRA_ID

Get stories for a specific team:

.. code-block:: bash

    python get_jira_stories.py -t "Your Team Name"

Get stories for a different fix version:

.. code-block:: bash

    python get_jira_stories.py -f "NTWK.26.PI1"

On Windows, refresh an Excel file with the data:

.. code-block:: bash

    python get_jira_stories.py --excel-file path/to/your/file.xlsx
"""

import argparse
import base64
import logging
import os
import platform
import subprocess
import sys
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional
import re
import json
import ipdb  # For debugging purposes

import pandas as pd
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress insecure request warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class JiraConfig:
    """Configuration settings for Jira API access and queries."""
    # Jira API and field settings
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
    DATE_FORMAT_SHORT = "%Y-%m-%d"
    FIELDS = [
        "title",
        "link",
        "summary",
        "issuetype",
        "status",
        "assignee",
        "reporter",
        "created",
        "updated",
        "customfield_10020",  # Sprint field
        "customfield_10028",  # Story points field
        "customfield_11249",  # Teams field
        "parent",
        "fixVersions",
    ]

    def __init__(self, args):
        """Initialize configuration from command-line arguments and environment."""
        # Project and version settings
        self.base_url = f"https://{args.tenant}.atlassian.net/rest/api/3/search"

        self.project_name = args.project_name
        self.fix_version = args.fix_version

        # User identification
        self.jira_id = args.id or os.environ.get("JIRA_ID")
        self.jira_email = args.email or os.environ.get("JIRA_EMAIL")

        # Output settings
        self.output_file = args.output_file or f"jira-{self.fix_version}.csv"
        self.excel_file = args.excel_file or os.environ.get("JIRA_EXCEL")

        # Search parameters
        self.team_name = args.team_name
        self.epics_only = args.epics

        # Retrieve token securely
        self._token = None

        # Auto-detect email if needed
        if not self.jira_email:
            self._detect_email()

    def _detect_email(self):
        """Attempt to get email from git config if not provided."""
        logger = get_logger()
        try:
            self.jira_email = subprocess.check_output(
                ["git", "config", "--get", "user.email"], encoding="utf-8"
            ).strip()
            logger.info(f"Got email from git config: {self.jira_email}")
        except Exception:
            logger.error("Failed to get email from git config")
            raise RuntimeError(
                "Please provide email: set JIRA_EMAIL environment variable, "
                "configure git user.email, or use the -e command line option."
            )

    @property
    def token(self):
        """Get the JIRA API token, retrieving it if necessary."""
        if not self._token:
            self._token = os.environ.get("JIRA_TOKEN")
            if not self._token:
                logger = get_logger()
                logger.error("JIRA_TOKEN environment variable not set")
                raise EnvironmentError(
                    "Please set the JIRA_TOKEN environment variable with your Jira API token."
                )
        return self._token

    def update_output_file(self):
        """Update output filename based on search parameters."""
        # Update for team name
        if self.team_name and self.output_file == f"jira-{self.fix_version}.csv":
            self.output_file = f"jira-{self.fix_version}-{self.team_name}.csv"

        # Update for epics
        if self.epics_only and not self.output_file.endswith("-epics.csv"):
            self.output_file = self.output_file.replace(".csv", "-epics.csv")


# Logging setup
_logger = None


def get_logger(debug=False):
    """
    Get or create the logger for this application.

    Args:
        debug: Whether to enable debug logging

    Returns:
        The configured logger
    """
    global _logger

    if _logger is not None:
        if debug:
            _logger.setLevel(logging.DEBUG)
        return _logger

    logger = logging.getLogger("jira_stories")

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
    )

    # Console handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # File handler
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True, mode=0o755)
    logfilepath = os.path.join(log_dir, "get_jira_stories.log")
    file_handler = logging.FileHandler(logfilepath, mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Set log level
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.info(f"Log file: {logfilepath}")

    _logger = logger
    return logger


# Date and data extraction utilities
def parse_datetime(date_str: str) -> str:
    """
    Parse a datetime string from Jira API and format it to a short date format.

    Args:
        date_str: The datetime string to parse.

    Returns:
        The formatted date string in 'YYYY-MM-DD' format.
    """
    logger = get_logger()
    try:
        dt = datetime.strptime(date_str, JiraConfig.DATE_FORMAT)
        formatted_date = dt.strftime(JiraConfig.DATE_FORMAT_SHORT)
        logger.debug(f"Parsed date: {formatted_date}")
        return formatted_date
    except ValueError as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return date_str  # Return original if parsing fails


def extract_sprint(
    sprints: List[Dict[str, Any]]
) -> str:
    """
    Extract the sprint name for the custom field.

    Args:
        sprints: List of sprint data.

    Returns:
        The sprint name if found, None otherwise.
    """
    logger = get_logger()
    if not sprints:
        return None

    # Example sprint name format: NDO.25.PI3.S1
    sprint_name_re = re.compile(
        r"^NDO\.(\d+).PI(\d+)\.S(\d+)$"
    )

    for sprint in sprints:
        sprint_name = sprint.get("name", "")
        sprint_name_list = sprint_name.split(".")

        if len(sprint_name_list) < 4:
            continue

        sprint_fv_number = sprint_name_list[1:3]
        if re.match(sprint_name_re, sprint_name):
            # Check if the sprint matches the fix version format
            logger.debug(f"Found sprint: {sprint_name}")
            return sprint_name

    logger.debug(f"No sprint name found matching the fix version format")
    return None


def extract_field(data: Dict[str, Any], field: str, default: Any = None) -> Any:
    """
    Safely extract a field from nested dictionary data.

    Args:
        data: Dictionary containing the field
        field: The field to extract, can use dot notation for nested fields
        default: Default value if field not found

    Returns:
        Field value or default if not found
    """
    if not data:
        return default

    if "." not in field:
        return data.get(field, default)

    # Handle nested fields like "parent.key"
    parts = field.split(".")
    current = data

    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]

    return current if current is not None else default


# Jira API communication
def build_jql_query(config: JiraConfig) -> str:
    """
    Build the JQL query based on configuration parameters.

    Args:
        config: The Jira configuration

    Returns:
        JQL query string
    """
    logger = get_logger()

    # Start with project and fix version
    jql = f"project = {config.project_name} AND fixVersion = '{config.fix_version}' "

    # Add filter for team or assignee
    if config.team_name:
        field = "Teams" if config.epics_only else "Agile Team"
        team_value = (
            f"NTWK - {config.team_name}" if config.epics_only else config.team_name
        )
        jql += f"AND '{field}' in ('{team_value}') "
    elif config.jira_id:
        jql += (
            f'AND (assignee = {config.jira_id} OR "Assignees[User Picker (multiple users)]" '
            f"IN ({config.jira_id})) "
        )

    # Add epic filter if requested
    if config.epics_only:
        jql += f"AND 'issuetype' = 'Epic' "

    logger.debug(f"JQL query: {jql}")
    return jql


def make_jira_request(
    config: JiraConfig, jql: str, start_at: int = 0, max_results: int = 50
) -> Dict[str, Any]:
    """
    Make a request to the Jira API.

    Args:
        config: The Jira configuration
        jql: JQL query to execute
        start_at: Pagination start position
        max_results: Maximum number of results to return

    Returns:
        JSON response from the API

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If the response is not valid JSON
    """
    logger = get_logger()

    # Build URL with parameters
    field_string = ",".join(JiraConfig.FIELDS)
    encoded_jql = urllib.parse.quote(jql)
    url = (
        f"{config.base_url}?startAt={start_at}&maxResults={max_results}"
        f"&fields={field_string}&jql={encoded_jql}"
    )

    # Build authentication headers
    auth_str = f"{config.jira_email}:{config.token}"
    encoded_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Log request details
    logger.info(
        f"Fetching Jira data for project {config.project_name}, fix version {config.fix_version}"
    )
    logger.debug(f"Request URL: {url[:20]}...{url[-20:]}")
    logger.debug(f"Authorization: Basic {encoded_auth[:5]}...{encoded_auth[-5:]}")

    # Make request
    try:
        response = requests.get(url, headers=headers, verify=False)

        # Handle error status codes
        if response.status_code != 200:
            logger.error(f"Request failed with status code: {response.status_code}")
            logger.error(f"Response headers: {response.headers}")
            logger.error(f"Response content: {response.text}")
            response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Validate response structure
        for key in ["issues", "total"]:
            if key not in data:
                raise ValueError(f"Invalid API response: missing '{key}' key")

        if not isinstance(data["issues"], list):
            raise ValueError("Invalid API response: 'issues' is not a list")

        if not isinstance(data["total"], int):
            raise ValueError("Invalid API response: 'total' is not an integer")

        return data

    except requests.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise


def fetch_all_jira_issues(config: JiraConfig) -> List[Dict[str, Any]]:
    """
    Fetch all Jira issues matching the criteria, handling pagination.

    Args:
        config: The Jira configuration

    Returns:
        List of all matching Jira issues
    """
    logger = get_logger()

    # Update output filename based on parameters
    config.update_output_file()

    # Build JQL query
    jql = build_jql_query(config)

    # Fetch all issues with pagination
    start_at = 0
    max_results = 50
    all_issues = []

    while True:
        # Make the API request
        data = make_jira_request(config, jql, start_at, max_results)
        issues = data["issues"]
        total = data["total"]

        # Add results to our collection
        all_issues.extend(issues)

        # Log progress
        logger.info(f"Retrieved {len(issues)} issues, total: {total}")

        # Check if we've retrieved all issues
        if len(issues) == 0 or start_at + max_results >= total:
            logger.info(f"Retrieved all {total} issues")
            break

        # Prepare for next page
        start_at += max_results

    return all_issues


# Data processing functions
def process_jira_data(
    issues: List[Dict[str, Any]], fix_version: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process Jira issues into a simplified format for reporting.

    Args:
        issues: Raw issues from the Jira API
        fix_version: Fix version being processed

    Returns:
        List of processed issues with extracted data
    """
    logger = get_logger()
    processed_issues = []

    for issue in issues:
        try:
            fields = issue["fields"]

            # Extract basic fields
            processed_issue = {
                "key": issue["key"],
                "summary": extract_field(fields, "summary", "No summary"),
                "points": fields.get("customfield_10028"),
                "created": parse_datetime(fields["created"])
                if "created" in fields
                else None,
                "updated": parse_datetime(fields["updated"])
                if "updated" in fields
                else None,
                "reporter_email": extract_field(
                    fields, "reporter.emailAddress", "Unknown"
                ),
                "assignee_email": extract_field(
                    fields, "assignee.emailAddress", "Unassigned"
                ),
                "sprint": extract_sprint(fields.get("customfield_10020")),
                "status": extract_field(fields, "status.name", "Unknown"),
                "parent": extract_field(fields, "parent.key", "No parent"),
                "issuetype": extract_field(fields, "issuetype.name", "Unknown"),
                "fixVersions": ",".join([extract_field(
                    fv, "name", "Unknown"
                ) for fv in fields.get("fixVersions", [])]),
            }

            processed_issues.append(processed_issue)

        except KeyError as e:
            logger.warning(f"Missing field in issue {issue.get('key', 'unknown')}: {e}")
            ipdb.set_trace()
        except Exception as e:
            logger.error(f"Error processing issue {issue.get('key', 'unknown')}: {e}")
            raise

    logger.debug(f"Returning {len(processed_issues)} issues")
    return processed_issues


# Export and reporting functions
def export_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Export the processed data to a CSV file.

    Args:
        data: The data to export
        filename: The output filename

    Raises:
        IOError: If writing to the file fails
    """
    logger = get_logger()

    try:
        # Convert to pandas DataFrame and save
        df = pd.DataFrame(data)
        logger.debug(f"Columns in DataFrame: {df.columns.tolist()}")
        df.to_csv(filename, index=False)
        logger.info(f"Data exported to {filename}")
    except Exception as e:
        logger.error(f"Failed to export data to CSV: {e}")
        raise IOError(f"Failed to write to {filename}: {e}")


def refresh_excel_data(excel_file: str) -> None:
    """
    Refresh data connections in an Excel file (Windows only).

    Args:
        excel_file: Path to the Excel file to refresh
    """
    logger = get_logger()

    # Check if we're on Windows
    if platform.system() != "Windows":
        logger.warning("Excel refresh only supported on Windows")
        return

    # Validate the Excel file
    if not os.path.isfile(excel_file):
        logger.error(f"Excel file not found: {excel_file}")
        return

    if not os.path.splitext(excel_file)[1].lower().startswith(".xls"):
        logger.error(f"Not an Excel file: {excel_file}")
        return

    try:
        # Import Windows-specific modules
        import xlwings as xw
        from win32com.client import Dispatch

        # Open workbook and refresh
        logger.info(f"Opening Excel file: {excel_file}")
        wb = xw.Book(excel_file)

        logger.info("Refreshing all data connections")
        wb.api.RefreshAll()

        # Wait for refresh to complete
        logger.info("Waiting for refresh to complete")
        xl = Dispatch("Excel.Application")
        xl.CalculateUntilAsyncQueriesDone()

        # Save and close
        logger.info("Refresh complete. Saving workbook")
        wb.save()

    except ImportError:
        logger.error("xlwings and win32com.client required for Excel operations")
    except Exception as e:
        logger.error(f"Excel refresh failed: {e}")


# CLI argument parsing
def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        Parsed argument namespace
    """
    parser = argparse.ArgumentParser(
        description="Jira Stories Retrieval Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Core arguments
    parser.add_argument("-i", "--id", help="Jira account ID for the assignee")
    parser.add_argument(
        "-e", "--email", help="Jira account email", default=os.environ.get("JIRA_EMAIL")
    )
    parser.add_argument(
        "-f",
        "--fix-version",
        default="NTWK.25.PI3",
        help="Fix version to filter stories",
    )
    parser.add_argument(
        "-p", "--project-name", default="NTWK", help="Jira project name"
    )
    parser.add_argument(
        "--tenant", default="marriottcloud", help="Jira tenant name"
    )
    # Search options
    parser.add_argument(
        "-t", "--team_name", help="Search by team name instead of assignee"
    )
    parser.add_argument("--epics", action="store_true", help="Include only epics")
    parser.add_argument("--parse_only", action="store_true", help="Parse only, do not fetch data")
    parser.add_argument("--input_file", help="Input JSON file to parse (for --parse_only)")
    # Output options
    parser.add_argument("-o", "--output-file", help="Output CSV filename")
    parser.add_argument(
        "--excel-file",
        help="Excel file to refresh (Windows only)",
        default=os.environ.get("JIRA_EXCEL"),
    )

    # Debug option
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    # Parse arguments
    args = parse_arguments()

    # Configure logging
    logger = get_logger(args.debug)
    logger.info("Starting Jira Stories Retrieval Tool")

    # Validate required arguments
    if (not args.id and args.team_name) and not args.parse_only:
        logger.error("Please provide either --id or --team_name")
        raise RuntimeError(
            "You must specify either --id for assignee or --team_name for team search."
        )
    if args.parse_only and not args.input_file:
        logger.error("Please provide --input_file when using --parse_only")
        raise RuntimeError(
            "When using --parse_only, you must specify --input_file with the JSON data."
        )

    try:
        # Initialize configuration
        config = JiraConfig(args)

        # Fetch and process Jira data
        if args.parse_only:
            try:
                with open(args.input_file, "r") as f:
                    jdata = json.load(f)
                    all_issues = jdata.get("issues", [])
                if not all_issues or not isinstance(all_issues, list):
                    logger.error(f"Invalid input file format: {args.input_file}")
                    logger.error(f"type(all_issues): {type(all_issues)}")
                    logger.error(f"len(all_issues): {len(all_issues)}")
                    raise ValueError(
                        f"Invalid input file format: {args.input_file}. "
                    )
            except Exception as e:
                logger.error(f"Failed to read input file {args.input_file}: {e}")
                raise
            processed_data = process_jira_data(all_issues)
            logger.info(f"Parsed {len(all_issues)} issues from input file: {args.input_file}")
        else:
            # Fetch all issues from Jira
            all_issues = fetch_all_jira_issues(config)
            if not all_issues:
                logger.warning("No issues found matching the criteria")
                return
            processed_data = process_jira_data(all_issues, config.fix_version)
            logger.info(f"Parsed {len(all_issues)} issues from JIRA API")
        # Export to CSV
        export_to_csv(processed_data, config.output_file)

        # Refresh Excel if requested and on Windows
        if config.excel_file and not args.parse_only and platform.system() == "Windows":
            logger.info(f"Refreshing Excel file: {config.excel_file}")
            refresh_excel_data(config.excel_file)

    except Exception as e:
        logger.error(f"Error: {e.__class__.__name__}: {e}")
        sys.exit(1)

    logger.info("Jira data processing completed successfully")


if __name__ == "__main__":
    main()
