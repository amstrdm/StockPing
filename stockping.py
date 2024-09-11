import requests
from bs4 import BeautifulSoup
import time
import json
import os
import argparse

def create_config():
    press_url = input("Please enter the url of the press release site of the company you want to track (note: this is only going to be asked once, if you want to change this later execute the script with a '--url yoururl' flag): ")
    webhook_url = input("Please enter the url of your webhook (note: this is only going to be asked once, if you want to change this value later on execute the script with an added '--webhook yourwebhook' flag): ")
    date_selector = input("Please enter the CSS selector for publication dates (optional): ")
    
    try:
        num_links_input = input("Enter the amount of links that should be checked if date-based checking fails (default: 50): ")
        num_links = int(num_links_input) if num_links_input.strip() else 50
    except ValueError:
        print("Invalid Input, defaulting to 50 links.")
        num_links = 50
    
    config = {
        "url": press_url,
        "notify_url": webhook_url,
        "date_selector": date_selector,
        "num_links": num_links 
    }
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)
    print("Config file created.")


def load_config():
    config_file = "config.json"
    
    # Check if the file exists and is not empty
    if not os.path.exists(config_file):
        # prompt user for values if config file doesn't exist or is empty
        create_config()
    #if it exists but is empty remove it and reinitialize
    elif os.path.getsize(config_file) == 0:
        os.remove(config_file)
        create_config()
    
    # Load the configuration from the file
    with open(config_file, "r") as file:
        config = json.load(file)
        
        # Check if both keys exist and are not empty
        url = config.get("url")
        notify_url = config.get("notify_url")
        date_selector = config.get("date_selector")
        num_links = config.get("num_links")
        
        if url and notify_url:
            return url, notify_url, date_selector, num_links
        else:
            raise ValueError("Config file is missing 'url' or 'notify_url' (try deleting the config file)")


def check_new_links(url, last_links, num_links, date_selector=None,):
    # i hate request error handling so much but here we go
    try:
        # Attempt to fetch the page
        response = requests.get(url, timeout=10)  # Setting a timeout to avoid hanging
        response.raise_for_status()  # This will raise an HTTPError if the status is 4xx or 5xx
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP error
        return None, [], last_links
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Error connecting to {url}: {conn_err}")  # Connection error
        return None, [], last_links
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout occurred while trying to access {url}: {timeout_err}")  # Timeout error
        return None, [], last_links
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")  # Any other requests-related error
        return None, [], last_links
    
    soup = BeautifulSoup(response.text, "html.parser")

    if date_selector:
        try:
            dates = [a.text.strip() for a in soup.select(date_selector)]
            links = [a["href"] for a in soup.select(date_selector).parent.select("a[href]")]  # Adjust if necessary
        except:
            print("Failed to extract dates/links based to dates. Falling back to link-based checking.")
            return(check_new_links(url, last_links, num_links))
        
        if len(dates) != len(links):
            # Fallback if date and link counts do not match
            print("Date extraction inconsistent with links. Falling back to link-based checking.\n")
            return check_new_links(url, last_links, num_links)  # Recursive call to fallback

        link_date_pairs = list(zip(links, dates))
        link_date_pairs.sort(key=lambda x: x[1], reverse=True)  # Sort by date (latest first)
        links = [link for link, _ in link_date_pairs]

        added_links = [link for link in links if link not in last_links]
        new_press_release_link = links[0] if added_links else None

    else:
        # Fallback to link-based checking
        links = [a["href"] for a in soup.find_all("a", href=True)[:num_links]]  # Limit to num_links
        added_links = [link for link in links if link not in last_links]
        new_press_release_link = links[0] if added_links else None
    print(f"URL: {url}\nNew press release link: {new_press_release_link}\n")
    return new_press_release_link, added_links, links

def send_notification(new_link, notify_url, max_retries=3):
    data = {"press_release_link": new_link}
    
    # again i hate this
    for attempt in range(max_retries):
        try:
            response = requests.post(notify_url, json=data, timeout=10)  # Timeout to avoid hanging requests
            response.raise_for_status()  # Raise an exception for bad status codes (4xx, 5xx)
            
            if response.status_code == 200:
                print(f"Notification sent successfully for {new_link}")
                return True
            else:
                print(f"Unexpected status code {response.status_code} from the webhook.")
        
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} (Status code: {response.status_code})")
        
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Error connecting to the webhook URL: {conn_err}")
        
        except requests.exceptions.Timeout:
            print(f"Timeout occurred while sending notification to {notify_url}")
        
        except requests.exceptions.RequestException as req_err:
            print(f"An unexpected error occurred: {req_err}")

        # If the webhook request fails, retry after a short delay
        print(f"Retrying... ({attempt + 1}/{max_retries})")
        time.sleep(5)  # Wait 5 seconds before retrying
    
    print(f"Failed to send notification after {max_retries} attempts.")
    return False


def update_config(new_url=None, new_notify_url=None, new_date_selector=None, new_num_links = None):
    url, notify_url, date_selector, num_links = load_config()
    
    config = {
        "url": new_url if new_url else url,
        "notify_url": new_notify_url if new_notify_url else notify_url,
        "date_selector": new_date_selector if new_date_selector else date_selector,
        "num_links": new_num_links if new_num_links else num_links
    }
    
    # Write the updated config back to the file
    with open("config.json", "w") as file:
        json.dump(config, file, indent=4)
    print("Config file updated.")




print("type '--help' when running the script for a list of the optional flags\n")

# Define optional CLI arguments
parser = argparse.ArgumentParser(description="Monitor a press release site.")

parser.add_argument("--url", type=str, help="Set a new URL for press releases.")
parser.add_argument("--webhook", type=str, help="Set a new notification webhook URL.")
parser.add_argument("--date-selector", type=str, help="Set a new CSS selector for publication dates.")
parser.add_argument("--delay", type=int, help="Set the time between each check for a new press release.")
parser.add_argument("--num-links", type=int, help="Set the number of links which will be checked in case date checking fails.")

args = parser.parse_args()

# Update the config if arguments are passed
if args.url or args.webhook or args.date_selector or args.num_links:
    update_config(new_url=args.url, new_notify_url=args.webhook, new_date_selector=args.date_selector, new_num_links=args.num_links)
else:
    # If no arguments are passed, just load and print the config
    try:
        url, notify_url, date_selector, num_links = load_config()
        print(f"Current Config: URL: {url}, Notify URL: {notify_url}, Date Selector: {date_selector}, Links to be checked: {num_links}")
        if date_selector == "":
            print("No CSS selector given. Falling back to link-based checking.\n")
    except ValueError as e:
        print(e)

#check if a delay is specified otherwise just use the default delay
delay = args.delay if args.delay else 15

# Track links seen
last_links = []

while True:
    try:
        new_press_release_link, added_links, all_links = check_new_links(url=url, last_links=last_links, num_links=num_links, date_selector=date_selector)
    
        if new_press_release_link and last_links != []:
            print(f"New Press release found: {new_press_release_link}")
            send_notification(new_press_release_link, notify_url)
        
        #update list of seen links
        last_links = all_links
    
    except Exception as e:
        print(f"Error checking for new links: {e}")
    
    time.sleep(delay)