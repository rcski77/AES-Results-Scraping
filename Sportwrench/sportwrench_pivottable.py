from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pandas as pd


def extract_division_ids(url):
    """
    Uses Selenium to find all division links on the given page and extract the division IDs.

    Args:
        url (str): The URL of the SportWrench event divisions page.

    Returns:
        list: A list of extracted division IDs.
    """
    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    # Specify the path to your ChromeDriver
    service = Service(r"C:\Git Repos\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to the URL
        driver.get(url)

        # Wait for the page to load completely (adjust timeout as necessary)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a[href*='/divisions/']")))

        # Find all anchor tags with href attributes containing '/divisions/'
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/divisions/']")

        # Extract and parse division IDs from the hrefs
        division_ids = []
        for link in links:
            href = link.get_attribute("href")
            match = re.search(r"/divisions/(\d+)$", href)
            if match:
                division_ids.append(match.group(1))

        return division_ids
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        # Quit the driver
        driver.quit()


def extract_standings(event_id, division_id):
    """
    Extracts the standings (rank and team name) for a given division ID.

    Args:
        event_id (str): The event ID.
        division_id (str): The division ID.

    Returns:
        list: A list of dictionaries containing rank and team name.
    """
    # Set up Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--enable-unsafe-swiftshader")

    # Specify the path to your ChromeDriver
    service = Service(r"C:\Git Repos\chromedriver-win64\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        standings_url = f"https://events.sportwrench.com/#/events/{
            event_id}/divisions/{division_id}/standings"
        driver.get(standings_url)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".standings-team-name")))

       # Find all rows in the table (except the header row)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")[
            1:]  # Skip header row

        standings = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 3:  # Ensure there are enough cells
                finish = cells[0].text.strip()  # First column: Finish
                team_name = cells[1].text.strip()  # Second column: Team Name
                # Second to Last column: Code
                code = cells[-2].text.strip().lower()
                standings.append({
                    "Finish": finish,
                    "Team Name": team_name,
                    "Code": code
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
        wait.until(EC.presence_of_element_located(
            # Wait for the element with the class esw_title
            (By.CLASS_NAME, "esw_title")))

        # Extract the event name (assuming it's in an element with class 'esw_title')
        event_name = driver.find_element(
            By.CLASS_NAME, "esw_title").text.strip()
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
    # Extract the event name
    event_name = extract_event_name(url)
    print(f"Extracted Event Name: {event_name}")

    # Append '/divisions' to the event URL
    divisions_url = f"{url.rstrip('/')}/divisions"
    print(f"Fetching divisions from: {divisions_url}")

    # Extract division IDs
    division_ids = extract_division_ids(divisions_url)

    if not division_ids:
        print("No division IDs found.")
        return

    # Extract the event ID from the URL
    match = re.search(r"events/([a-z0-9]+)", url)
    if not match:
        print("Invalid event URL format. Unable to extract event ID.")
        return
    event_id = match.group(1)

    # Collect all standings data
    all_standings = []
    for division_id in division_ids:
        print(f"Fetching standings for division ID: {division_id}")
        standings = extract_standings(event_id, division_id)
        if standings:
            # Add division ID and event name to each standing
            for standing in standings:
                standing["Event Name"] = event_name
                standing["Division ID"] = division_id
            all_standings.extend(standings)
        else:
            print(f"No standings found for Division {division_id}")

    # Create a DataFrame from the standings
    df = pd.DataFrame(all_standings)
    if df.empty:
        print("No standings data collected.")
        return

    # Pivot the data by team code and use event name as column header
    pivoted_df = df.pivot_table(
        index="Code",  # Use team code as the index
        columns="Event Name",  # Use event name as the column
        values="Finish",  # Use finish as the values
        aggfunc="first"  # If duplicates, take the first
    ).reset_index()

    # Export the pivoted data to a CSV file
    csv_file_path = "event_standings_with_event_name.csv"
    pivoted_df.to_csv(csv_file_path, index=False)
    print(f"Pivoted standings saved to {csv_file_path}")


# Example usage
event_url = "https://events.sportwrench.com/#/events/6583cabd2"
process_event(event_url)
