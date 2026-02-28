# GEMINI.md

## Directory Overview

This directory contains a shell script, `fetch_text.sh`, designed to retrieve bible verses from the `bible.fhl.net` API. The script is the primary component of this directory, suggesting a focus on data retrieval and processing related to biblical texts.

## Key Files

*   **`fetch_text.sh`**: A bash script that fetches bible verses. It accepts arguments for the book, chapter, and section in either Chinese or English. It then makes API calls to `bible.fhl.net` and formats the JSON response.

## Usage

The `fetch_text.sh` script is the main utility in this directory.

### Dependencies

*   `curl`: To make HTTP requests to the API.
*   `jq`: To process the JSON response.

### How to Run

You can run the script from the command line, providing the book, chapter, and verse you want to retrieve.

**Examples:**

*   Fetch John 3:16 (default):
    ```bash
    ./fetch_text.sh
    ```
*   Fetch Genesis 1:1 using the English abbreviation:
    ```bash
    ./fetch_text.sh --engs Gen --chap 1 --sec 1
    ```
*   Fetch John 1:1 using the Chinese name:
    ```bash
    ./fetch_text.sh --chineses 約 --chap 1 --sec 1
    ```
*   List all supported book abbreviations:
    ```bash
    ./fetch_text.sh --list
    ```
