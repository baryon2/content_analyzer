#!/usr/bin/env python3
"""
Enhanced Content Scanner using ripgrep and JSON configuration
This script provides better detection with fewer false positives
"""

import json
import os
import subprocess
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any
import csv

def load_config(config_path):
    """Load configuration from JSON file"""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file not found at {config_path}")
        exit(1)

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        exit(1)

def clone_repo(repo_url, repos_dir):
    """Clone repository if it doesn't exist"""
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = os.path.join(repos_dir, repo_name)

    # Convert HTTPS to SSH if needed
    actual_clone_url = repo_url
    if repo_url.startswith("https://github.com/"):
        actual_clone_url = repo_url.replace("https://github.com/", "git@github.com:")
        if not actual_clone_url.endswith(".git"):
            actual_clone_url += ".git"

    if not os.path.exists(repo_path):
        print(f"Cloning {actual_clone_url}...")
        try:
            subprocess.run(["git", "clone", actual_clone_url, repo_path],
                         check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to clone {actual_clone_url}: {e.stderr}")
            return None
    else:
        print(f"Repository {repo_name} already exists. Skipping clone.")

    return repo_path

def should_ignore_line(line: str, ignore_patterns: List[str]) -> bool:
    """Check if line should be ignored based on patterns"""
    for pattern in ignore_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False

def scan_with_ripgrep(repo_path: str, patterns: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Use ripgrep to scan for patterns"""
    findings = []

    # Build file type arguments for ripgrep
    type_args = []
    for ext in config.get('file_extensions', []):
        type_args.extend(['-g', f'*{ext}'])

    # Build exclude directory arguments
    for exclude_dir in config.get('exclude_dirs', []):
        type_args.extend(['-g', f'!{exclude_dir}/'])

    # Build exclude file arguments
    for exclude_file in config.get('exclude_files', []):
        type_args.extend(['-g', f'!{exclude_file}'])

    ignore_patterns = config.get('ignore_line_patterns', [])

    for category, category_data in patterns.items():
        print(f"  Scanning for {category} ({category_data.get('description', '')})...")
        category_patterns = category_data.get('patterns', [])

        for pattern in category_patterns:
            # Use word boundaries for better matching
            word_pattern = rf'\b{re.escape(pattern)}\b'

            try:
                # Run ripgrep with the pattern
                cmd = [
                    'rg',
                    '--line-number',
                    '--no-heading',
                    '-i',  # Case insensitive
                    '--color', 'never',
                    word_pattern
                ] + type_args + [repo_path]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:  # Found matches
                    for line in result.stdout.strip().split('\n'):
                        if not line:
                            continue

                        # Parse ripgrep output: filepath:line_number:line_content
                        parts = line.split(':', 2)
                        if len(parts) >= 3:
                            file_path = parts[0]
                            line_number = parts[1]
                            line_content = parts[2]

                            # Check if line should be ignored
                            if should_ignore_line(line_content, ignore_patterns):
                                continue

                            # Find the actual matched text
                            match = re.search(word_pattern, line_content, re.IGNORECASE)
                            matched_text = match.group() if match else pattern

                            findings.append({
                                "file_path": file_path,
                                "line_number": int(line_number),
                                "category": category,
                                "pattern_found": pattern,
                                "line_content": line_content.strip(),
                                "matched_text": matched_text
                            })

            except subprocess.CalledProcessError as e:
                if e.returncode != 1:  # 1 means "no matches found" which is OK
                    print(f"Warning: ripgrep failed for pattern '{pattern}': {e}")
            except FileNotFoundError:
                print("Error: ripgrep (rg) not found. Please install ripgrep.")
                print("  macOS: brew install ripgrep")
                print("  Ubuntu/Debian: apt install ripgrep")
                exit(1)

    return findings

def scan_repository(repo_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scan a single repository"""
    patterns = config.get('categories', {})

    print(f"Scanning repository: {os.path.basename(repo_path)}")

    # Count files first for progress
    try:
        find_cmd = ['find', repo_path, '-type', 'f']
        # Add file extension filters
        ext_filters = []
        for ext in config.get('file_extensions', []):
            ext_filters.extend(['-name', f'*{ext}', '-o'])
        if ext_filters:
            ext_filters = ext_filters[:-1]  # Remove last '-o'
            find_cmd.extend(['('] + ext_filters + [')'])

        result = subprocess.run(find_cmd, capture_output=True, text=True)
        file_count = len([line for line in result.stdout.strip().split('\n') if line])
        print(f"  Found {file_count} files to scan...")
    except:
        print("  Scanning files...")

    findings = scan_with_ripgrep(repo_path, patterns, config)

    print(f"  Found {len(findings)} total issues")
    return findings

def convert_json_to_csv(json_file, csv_file, report):
    """Converts a JSON report of problematic content to a CSV file."""
    # Define CSV headers
    fieldnames = ["repository", "file_path", "line_number", "category", "pattern_found", "line_content", "matched_text"]

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
                    "line_content": finding.get("line_content", ""),
                    "matched_text": finding.get("matched_text", "")
                }
                writer.writerow(row)
    print(f"Conversion complete. Report saved to {csv_file}")

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



def main():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    default_config_path = os.path.join(script_dir, 'simple_config.json')

    parser = argparse.ArgumentParser(description="Enhanced repository content scanner")
    parser.add_argument("--file", type=str, required=True, help="Path to a CSV or TXT file with a list of repository URLs.")
    parser.add_argument("--config", type=str, default=default_config_path,
                       help=f"Path to configuration file (default: {default_config_path})")
    parser.add_argument("--output", type=str, default="enhanced_content_report", help="Base name for output files (e.g., 'my_scan' will produce 'my_scan.json' and 'my_scan.csv')")
    parser.add_argument("--repos-dir", type=str, default="repos/cloned", help="Directory to clone repositories into.")
    parser.add_argument("--results-dir", type=str, default="enhanced_results", help="Directory to save scan reports.")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Create results directory
    os.makedirs(args.results_dir, exist_ok=True)

    # Determine repositories to scan
    repos_to_scan = fetch_repos_from_file(args.file)

    if not repos_to_scan:
        print("No repositories to scan. Please provide a valid file with repository URLs.")
        return

    # Ensure repos directory exists
    os.makedirs(args.repos_dir, exist_ok=True)

    # Show configuration summary
    total_patterns = sum(len(cat_data.get('patterns', [])) for cat_data in config.get('categories', {}).values())
    print(f"Enhanced Content Scanner")
    print(f"  Categories: {len(config.get('categories', {}))}")
    print(f"  Total patterns: {total_patterns}")
    print(f"  File extensions: {len(config.get('file_extensions', []))}")
    print(f"  Using ripgrep for fast scanning")
    print()

    # Scan repositories
    report = {}
    for repo in repos_to_scan:
        repo_url = repo.get("url")
        if not repo_url:
            continue

        repo_name = repo.get('name', repo_url.split('/')[-1].replace('.git', ''))
        repo_path = clone_repo(repo_url, args.repos_dir)

        if repo_path:
            findings = scan_repository(repo_path, config)
            if findings:
                report[repo_name] = findings
            else:
                print(f"  No issues found in {repo_name}")
            print()

    # Save reports
    json_output_file = os.path.join(args.results_dir, f"{args.output}.json")
    csv_output_file = os.path.join(args.results_dir, f"{args.output}.csv")

    with open(json_output_file, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Scan complete. JSON report saved to {json_output_file}")

    convert_json_to_csv(json_output_file, csv_output_file, report)


    # Summary
    total_findings = sum(len(findings) for findings in report.values())
    print(f"Total issues found: {total_findings}")

    # Show breakdown by category
    if total_findings > 0:
        category_counts = {}
        for findings in report.values():
            for finding in findings:
                category = finding['category']
                category_counts[category] = category_counts.get(category, 0) + 1

        print("\nBreakdown by category:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} issues")

if __name__ == "__main__":
    main()