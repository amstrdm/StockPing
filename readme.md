# Universal Press Release Tracker

This Python script monitors a company’s press release webpage for new posts. It is designed to work universally across different websites with minimal configuration, using either a date-based approach (preferred) or a fallback link-based approach when necessary.

## Features

- **Date-based press release detection**: The script uses the provided CSS selector to check for the publication dates of press releases. This is the most accurate method, as dates are typically consistent across press release pages.
- **Fallback to link-based detection**: If date-based detection fails (or isn't specified), the script defaults to tracking the first N links (default: 50) on the webpage, watching for any changes that might indicate a new press release.
- **Webhook notifications**: When a new press release is detected, a notification is sent to the specified webhook URL with the relevant link.
- **Configurable settings**: The script saves and loads settings (URL, webhook URL, date selector, number of links to check, etc.) from a `config.json` file, and supports command-line arguments for easy updates.

## How It Works

### 1. **Date-based Checking** (Preferred)

Most company press release pages include the publication dates for their press releases. This script utilizes the `date_selector` (a CSS selector) provided by the user to extract the dates and links from the webpage. It then compares the dates to detect new content.

- If a date selector is provided, the script:
    1. Scrapes the page for dates and associated links.
    2. Sorts press releases by the latest date.
    3. Sends a notification with the link to the new press release if a change is detected.

### 2. **Link-based Checking** (Fallback)

In cases where:

- The user does not provide a date selector.
- The dates and links on the page do not align (e.g., incorrect parsing).

The script defaults to checking the first N links (default is 50) on the page, assuming that at least one of them will point to the press release section.

**Note**: The fallback method is less accurate. It simply tracks whether any of the first N links change. If a change is detected, it assumes a new press release has been posted and sends a notification. However, the link provided may not be the correct one.

## Requirements

- To install requirements: 
    
    `pip install -r requirements.txt`
Or:
	`pip install requests beautifulsoup4`

## Configuration

When you first run the script, it will prompt you for:

- The URL of the company’s press release page.
- A webhook URL where notifications should be sent.
- A CSS selector for extracting dates (optional, but recommended).
- The number of links to check if date-based checking fails (optional, default: 50).

These values are stored in a `config.json` file for future runs, so you only need to provide them once. You can update them later via command-line arguments.

## Command-Line Usage

The script supports the following command-line options:

`python script.py [--url NEW_URL] [--webhook NEW_WEBHOOK] [--date-selector CSS_SELECTOR] [--delay SECONDS] [--num-links NUM_LINKS]`

### Options:

- `--url`: Change the URL of the press release page.
- `--webhook`: Update the webhook URL for notifications.
- `--date-selector`: Specify a new CSS selector for date extraction.
- `--delay`: Set the delay between each check (in seconds). Default: 15 seconds.
- `--num-links`: Set the number of links to check in fallback mode (if date checking fails).

## Example

To run the script:

`python script.py`

To change the URL or webhook:

`python script.py --url https://example.com/press-releases --webhook https://your-webhook-url.com`

To update the CSS selector for date checking:

`python script.py --date-selector ".press-release-date"`

## How to Use

1. Run the script for the first time to set up your configuration.
2. The script will continuously monitor the press release page at regular intervals (default is every 15 seconds).
3. If a new press release is detected (based on either date or link changes), a notification will be sent to the specified webhook URL.

## Notifications

Whenever the script detects a new press release, it sends a POST request to the webhook URL with the following data:

`{   "press_release_link": "https://example.com/new-press-release" }`

## Error Handling

- If the script encounters errors while accessing the press release page (e.g., connection issues, timeouts), it will retry up to 3 times before skipping the current check.
- If the webhook fails (e.g., network issues, invalid response), the script retries the notification up to 3 times before giving up.