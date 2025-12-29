# Enhanced Repository Content Scanner

This script provides an enhanced content scanning mechanism for Git repositories, leveraging `ripgrep` for fast and efficient pattern matching. It can scan multiple repositories from a provided list, analyze their content based on a configurable set of patterns, and generate detailed reports in both JSON and CSV formats.

## Features

*   **Batch Scanning:** Scan multiple repositories by providing a list of URLs in a text or CSV file.
*   **Configurable Patterns:** Define custom categories, search patterns (including regular expressions), file extensions to include, and directories/files to exclude via a JSON configuration file.
*   **`ripgrep` Powered:** Utilizes the high-performance `ripgrep` tool for rapid content analysis.
*   **Detailed Reporting:** Generates comprehensive reports in JSON format, with an optional conversion to CSV for easier analysis.
*   **Portable Paths:** Configurable directories for cloning repositories and storing results, ensuring flexibility across different environments.
*   **Graceful Error Handling:** Skips repositories that fail to clone and continues with the scan.

## Prerequisites

Before running the script, ensure you have the following installed:

*   **Python 3:** The script is written in Python 3.
*   **`ripgrep` (rg):** A command-line search tool that recursively searches directories for a regex pattern.
    *   **macOS:** `brew install ripgrep`
    *   **Ubuntu/Debian:** `sudo apt install ripgrep`
    *   For other systems, refer to the [ripgrep installation guide](https://github.com/BurntSushi/ripgrep#installation).
*   **Git:** For cloning repositories.
*   **GitHub CLI (`gh`):** While not directly used in the current version of the combined script, it is good practice to have it installed if you plan to use `fetch_repos.py` separately or encounter repositories that require GitHub CLI authentication.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>/content-analysis
    ```
2.  **Ensure `simple_config.json` is available:** The script expects a configuration file. A default one is located at `simple_config.json`. You can modify this or create your own.

## Usage

The script `enhanced_scanner_json.py` is the main entry point for initiating a scan.

```bash
python3 enhanced_scanner_json.py --file <path_to_repo_list> [options]
```

### Command-Line Arguments

*   `--file <path_to_repo_list>` (Required): Path to a CSV or TXT file containing the list of repository URLs to scan. See "Input File Format" below for details.
*   `--config <path_to_config>` (Optional): Path to the JSON configuration file.
    *   *Default:* `simple_config.json` (relative to the script's location).
*   `--output <base_name>` (Optional): Base name for the output report files.
    *   *Default:* `enhanced_content_report` (will produce `enhanced_content_report.json` and `enhanced_content_report.csv`).
*   `--repos-dir <directory_path>` (Optional): Directory where repositories will be cloned.
    *   *Default:* `repos/cloned`
*   `--results-dir <directory_path>` (Optional): Directory where the JSON and CSV scan reports will be saved.
    *   *Default:* `enhanced_results`

### Example Usage

1.  **Create an input file** named `my_repos.txt` with repository URLs:

    ```
    https://github.com/owner/repo1
    https://github.com/owner/repo2
    git@github.com:owner/repo3.git
    ```

2.  **Run the scanner using default directories:**

    ```bash
    python3 enhanced_scanner_json.py \
      --file my_repos.txt \
      --output my_scan_results
    ```

    This command will:
    *   Read repository URLs from `my_repos.txt`.
    *   Clone repositories into the default `repos/cloned` directory.
    *   Perform the content analysis.
    *   Save a JSON report to `enhanced_results/my_scan_results.json`.
    *   Save a CSV report to `enhanced_results/my_scan_results.csv`.

3.  **Run the scanner using custom directories (optional):**

    ```bash
    python3 enhanced_scanner_json.py \
      --file my_repos.txt \
      --output my_scan_results \
      --repos-dir /tmp/my_cloned_repos \
      --results-dir ./my_scan_reports
    ```

    This command will:
    *   Read repository URLs from `my_repos.txt`.
    *   Clone repositories into `/tmp/my_cloned_repos`.
    *   Perform the content analysis.
    *   Save a JSON report to `./my_scan_reports/my_scan_results.json`.
    *   Save a CSV report to `./my_scan_reports/my_scan_results.csv`.

### Input File Format

The file specified by `--file` can be either a plain text file (`.txt`) or a CSV file (`.csv`).

*   **Text File (.txt):** Each line should contain a single repository URL.
    ```
    https://github.com/repo/one
    https://github.com/repo/two
    ```
*   **CSV File (.csv):** Must contain a column named `url` for the repository URLs. Other columns are ignored.
    ```csv
    name,url,description
    Repo One,https://github.com/repo/one,First repository
    Repo Two,https://github.com/repo/two,Second repository
    ```

## Configuration (`simple_config.json`)

The `simple_config.json` file defines the rules for content scanning. It includes:

*   `categories`: A dictionary where keys are category names (e.g., "profanity", "api_keys") and values contain:
    *   `description`: A human-readable description of the category.
    *   `patterns`: A list of strings or regular expressions to search for within the code.
*   `file_extensions`: A list of file extensions (e.g., `".js"`, `".py"`) to include in the scan.
*   `exclude_dirs`: A list of directory names to exclude from the scan.
*   `exclude_files`: A list of file names to exclude from the scan.
*   `ignore_line_patterns`: A list of patterns. If a line contains any of these patterns, it will be ignored even if it matches a `category` pattern.

**Example `simple_config.json` snippet:**

```json
{
  "categories": {
    "profanity": {
      "description": "Profanity and offensive language",
      "patterns": [
        "swearword1",
        "swearword2"
      ]
    },
    "api_keys": {
      "description": "Potential API keys and secrets",
      "patterns": [
        "API_KEY",
        "SECRET_TOKEN"
      ]
    }
  },
  "file_extensions": [".js", ".ts", ".py", ".md"],
  "exclude_dirs": ["node_modules", "dist"],
  "exclude_files": ["package-lock.json"],
  "ignore_line_patterns": ["// ignore-scan", "# noqa"]
}
```
