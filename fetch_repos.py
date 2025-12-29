import subprocess
import json
import argparse
import csv

def fetch_repos_from_file(file_path):
    """
    Fetches repositories from a given file (CSV or TXT).
    Assumes the file contains one repo URL per line, or for CSV, the URL is in a column named 'url'.
    """
    repos = []
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.csv'):
                reader = csv.DictReader(f)
                for row in reader:
                    if 'url' in row:
                        repos.append({'url': row['url'], 'name': row.get('name', row['url'].split('/')[-1])})
            else:
                for line in f:
                    line = line.strip()
                    if line:
                        repos.append({'url': line, 'name': line.split('/')[-1]})
        return repos
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def fetch_leap_wallet_repos():
    """
    Fetches all repositories from the leapwallet organization using the gh client.
    """
    command = [
        "gh",
        "repo",
        "list",
        "leapwallet",
        "--json",
        "name,url",
        "--limit",
        "1000",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)
        return repos
    except subprocess.CalledProcessError as e:
        print(f"Error fetching repositories: {e}")
        print(f"Stderr: {e.stderr}")
        return []
    except FileNotFoundError:
        print("Error: 'gh' command not found. Please ensure the GitHub CLI is installed and in your PATH.")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from gh command output.")
        return []

def main():
    parser = argparse.ArgumentParser(description="Fetch repository list.")
    parser.add_argument('--file', type=str, help='Path to a CSV or TXT file with a list of repository URLs.')
    args = parser.parse_args()

    if args.file:
        repos = fetch_repos_from_file(args.file)
    else:
        repos = fetch_leap_wallet_repos()

    if repos:
        # The output of this script is expected to be a JSON file `repos/repos.json`
        # by the `enhanced_scanner_json.py` script.
        # So, we will write the output to that file.
        output_file = 'repos/repos.json'
        try:
            with open(output_file, 'w') as f:
                json.dump(repos, f, indent=4)
            print(f"Successfully saved {len(repos)} repositories to {output_file}")
        except IOError as e:
            print(f"Error writing to {output_file}: {e}")

if __name__ == "__main__":
    main()