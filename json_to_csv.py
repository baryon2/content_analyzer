
import json
import csv
import os

JSON_FILE = "problematic_content_report_open-dev-data.git.json"
CSV_FILE = "problematic_content_report_open-dev-data.csv"

def convert_json_to_csv(json_file, csv_file):
    """Converts a JSON report of problematic content to a CSV file."""
    if not os.path.exists(json_file):
        print(f"Error: JSON report file not found at {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Define CSV headers
    fieldnames = ["repository", "file_path", "line_number", "category", "pattern_found", "line_content"]

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for repo_name, findings in report.items():
            for finding in findings:
                row = {
                    "repository": repo_name,
                    "file_path": finding.get("file_path", ""),
                    "line_number": finding.get("line_number", ""),
                    "category": finding.get("category", ""),
                    "pattern_found": finding.get("pattern_found", ""),
                    "line_content": finding.get("line_content", "")
                }
                writer.writerow(row)
    print(f"Conversion complete. Report saved to {csv_file}")

if __name__ == "__main__":
    convert_json_to_csv(JSON_FILE, CSV_FILE)
