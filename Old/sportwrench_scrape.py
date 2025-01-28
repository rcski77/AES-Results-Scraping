import requests
import re

def fetch_event_data(url):
    """
    Extracts the eventID from the given URL and fetches data from the SportWrench API.

    Args:
        url (str): The URL containing the eventID.

    Returns:
        dict or None: The JSON response from the API if successful, None otherwise.
    """
    # Extract the eventID using regex
    match = re.search(r"events/([a-z0-9]+)", url)
    if not match:
        print("Invalid URL format. Unable to extract eventID.")
        return None
    
    event_id = match.group(1)
    print(f"Extracted eventID: {event_id}")
    
    # API endpoint with the extracted eventID
    api_url = f"https://events.sportwrench.com/api/esw/{event_id}"
    
    # Headers to include in the API request
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
               "Upgrade-Insecure-Requests": "1",
               "DNT": "1",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.5",
               "Accept-Encoding": "gzip, deflate",
               "Authority": "events.sportwrench.com",
               "Cookie": "sw.sid=s%3AlpLVY5PXzvfmFdnrE1e0MlCY9oyAByag.v1V83gPNn8N0r0vpktTbuOUG8y8hWH%2F%2BdvBJ4nBc1UY"
               }
    
    # Fetch data from the API
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        print(f"Successfully fetched data for eventID: {event_id}")
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None

# Example usage
url = "https://events.sportwrench.com/#/events/6583cabd2"
event_data = fetch_event_data(url)

if event_data:
    # Do something with the event data (e.g., save to a file, process further, etc.)
    print(event_data)
