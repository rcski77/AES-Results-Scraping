from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pandas as pd


def extract_division_ids_and_names(url):
    """
    Uses Selenium to find all division links and extract the division IDs and their names.

    Args:
        url (str): The URL of the SportWrench event divisions page.

    Returns:
        list: A list of dictionaries containing division IDs and their names.
    """
    chrome_options = Options()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    service = Service(r"C:\Git Repos\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='/divisions/']")))

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/divisions/']")
        divisions = []
        for link in links:
            href = link.get_attribute("href")
            match = re.search(r"/divisions/(\d+)$", href)
            if match:
                division_id = match.group(1)
                division_name = link.text.strip()
                divisions.append({"Division ID": division_id, "Division Name": division_name})

        return divisions
    except Exception as e:
        print(f"An error occurred while extracting divisions: {e}")
        return []
    finally:
        driver.quit()


def extract_standings(event_id, division_id, division_name, event_name):
    """
    Extracts the standings (rank, team name, and code) for a given division ID.

    Args:
        event_id (str): The event ID.
        division_id (str): The division ID.
        division_name (str): The name of the division.
        event_name (str): The name of the event.

    Returns:
        list: A list of dictionaries containing rank, team name, code, division ID, division name, and event name.
    """
    chrome_options = Options()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    service = Service(r"C:\Git Repos\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        standings_url = f"https://events.sportwrench.com/#/events/{event_id}/divisions/{division_id}/standings"
        driver.get(standings_url)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".standings-team-name")))

        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")[1:]  # Skip the header row

        standings = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:  # Ensure there are enough cells
                finish = f"{cells[0].text.strip()} ({division_name})"
                team_name = cells[1].text.strip()
                code = cells[-2].text.strip().lower()
                standings.append({
                    "Finish": finish,
                    "Team Name": team_name,
                    "Code": code,
                    "Division ID": division_id,
                    "Division Name": division_name,
                    "Event Name": event_name
                })

        return standings
    except Exception as e:
        print(f"An error occurred while extracting standings: {e}")
        return []
    finally:
        driver.quit()


def extract_event_name(url):
    """
    Extracts the event name from the event page.

    Args:
        url (str): The URL of the SportWrench event page.

    Returns:
        str: The name of the event.
    """
    chrome_options = Options()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    service = Service(r"C:\Git Repos\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "esw_title")))

        event_name = driver.find_element(By.CLASS_NAME, "esw_title").text.strip()
        return event_name
    except Exception as e:
        print(f"An error occurred while extracting the event name: {e}")
        return "Unknown Event"
    finally:
        driver.quit()


def process_multiple_events(urls):
    """
    Processes multiple event URLs to extract standings and combine them based on team codes.

    Args:
        urls (list): A list of event URLs.

    Returns:
        None
    """
    all_data = []  # List to hold all standings data from all events

    for url in urls:
        event_name = extract_event_name(url)
        print(f"Processing Event: {event_name}")

        divisions_url = f"{url.rstrip('/')}/divisions"
        print(f"Fetching divisions from: {divisions_url}")

        divisions = extract_division_ids_and_names(divisions_url)
        if not divisions:
            print(f"No divisions found for event: {event_name}")
            continue

        match = re.search(r"events/([a-z0-9]+)", url)
        if not match:
            print(f"Invalid event URL format for {url}. Unable to extract event ID.")
            continue
        event_id = match.group(1)

        for division in divisions:
            division_id = division["Division ID"]
            division_name = division["Division Name"]
            print(f"Fetching standings for division: {division_name} (ID: {division_id}) in event {event_name}")
            standings = extract_standings(event_id, division_id, division_name, event_name)
            if standings:
                all_data.extend(standings)
            else:
                print(f"No standings found for Division {division_name} (ID: {division_id}) in event {event_name}")

    # Combine all standings into a DataFrame
    df = pd.DataFrame(all_data)
    if df.empty:
        print("No standings data collected across events.")
        return

    # Pivot the data by team code and use event names as columns
    pivoted_df = df.pivot_table(
        index="Code",  # Use team code as the index
        columns="Event Name",  # Use event names as the columns
        values="Finish",  # Use finish as the values
        aggfunc="first"  # If duplicates, take the first
    ).reset_index()

    # Export the combined data to a CSV file
    csv_file_path = "combined_event_standings.csv"
    pivoted_df.to_csv(csv_file_path, index=False)
    print(f"Combined standings saved to {csv_file_path}")


# Example usage
event_urls = [
    "https://events.sportwrench.com/#/events/6583cabd2",
    "https://events.sportwrench.com/#/events/abbfb1d13",
    "https://events.sportwrench.com/#/events/870cf0151",
    "https://events.sportwrench.com/#/events/7ccb7d73a",
    "https://events.sportwrench.com/#/events/aac1370ff",
    "https://events.sportwrench.com/#/events/e73a9d3b3",
    "https://events.sportwrench.com/#/events/c098ff439"
]
process_multiple_events(event_urls)
