from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


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
                code = cells[-2].text.strip().lower()  # Second to Last column: Code
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


def process_event(url):
    """
    Processes an event URL to extract division IDs and standings.

    Args:
        url (str): The base event URL.

    Returns:
        None
    """
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

    # Process standings for each division
    for division_id in division_ids:
        print(f"Fetching standings for division ID: {division_id}")
        standings = extract_standings(event_id, division_id)
        if standings:
            print(f"Standings for Division {division_id}:")
            for standing in standings:
                print(f"Rank: {standing['Finish']}, Team: {standing['Team Name']}, Code: {standing['Code']}")
        else:
            print(f"No standings found for Division {division_id}")


# Example usage
event_url = "https://events.sportwrench.com/#/events/6583cabd2"
process_event(event_url)