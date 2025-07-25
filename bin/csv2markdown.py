#!/usr/bin/env python3

import csv
import sys
import os

def csv_to_markdown(csv_file_path, markdown_file_path):
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        rows = list(reader)

    with open(markdown_file_path, 'w') as markdown_file:
        # Write the header row
        header = rows[0]
        markdown_file.write('| ' + ' | '.join(header) + ' |\n')
        markdown_file.write('|' + '---|' * len(header) + '\n')

        # Write the data rows
        for row in rows[1:]:
            markdown_file.write('| ' + ' | '.join(row) + ' |\n')

if __name__ == "__main__":
    csv_file_path = sys.argv[1]  # Replace with your CSV file path
    markdown_file_path = '/tmp/' + csv_file_path.replace('.csv', '.md')  # Replace with your desired Markdown file path
    csv_to_markdown(csv_file_path, markdown_file_path)
    os.system(f"code {markdown_file_path}")
