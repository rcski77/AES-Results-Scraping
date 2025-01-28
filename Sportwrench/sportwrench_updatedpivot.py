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
                division_name = link.text.strip()  # Get the text of the link as the division name
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
                finish = f"{cells[0].text.strip()} ({division_name})"  # Add division name in parentheses
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


def process_event(url):
    """
    Processes an event URL to extract division IDs, standings, and export to a CSV.

    Args:
        url (str): The base event URL.

    Returns:
        None
    """
    event_name = extract_event_name(url)
    print(f"Extracted Event Name: {event_name}")

    divisions_url = f"{url.rstrip('/')}/divisions"
    print(f"Fetching divisions from: {divisions_url}")

    divisions = extract_division_ids_and_names(divisions_url)
    if not divisions:
        print("No divisions found.")
        return

    match = re.search(r"events/([a-z0-9]+)", url)
    if not match:
        print("Invalid event URL format. Unable to extract event ID.")
        return
    event_id = match.group(1)

    all_standings = []
    for division in divisions:
        division_id = division["Division ID"]
        division_name = division["Division Name"]
        print(f"Fetching standings for division: {division_name} (ID: {division_id})")
        standings = extract_standings(event_id, division_id, division_name, event_name)
        if standings:
            all_standings.extend(standings)
        else:
            print(f"No standings found for Division {division_name} (ID: {division_id})")

    df = pd.DataFrame(all_standings)
    if df.empty:
        print("No standings data collected.")
        return

    csv_file_path = "event_standings_with_division_and_event_names.csv"
    df.to_csv(csv_file_path, index=False)
    print(f"Standings with division and event names saved to {csv_file_path}")


# Example usage
event_url = "https://events.sportwrench.com/#/events/6583cabd2"
process_event(event_url)
