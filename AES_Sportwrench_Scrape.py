import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
import requests
import pandas as pd

# First list of event IDs to process normally - current year's events
event_ids = [
    "PTAwMDAwMzY3NDY90",  # Central Zone
    "PTAwMDAwMzg4Mzk90",  # CO Challenge
    "PTAwMDAwMzcwNTU90",  # 2025 MLK 3 Step
    "PTAwMDAwMzY5NDk90",
    "PTAwMDAwMzczMjU90",
    "PTAwMDAwMzczMjY90",
    "PTAwMDAwMzcwODk90",
    "PTAwMDAwMzY5MTI90"
    # Add more event IDs here
]

# Second list of event IDs where TeamCodes will be incremented - last year's events
increment_teamcode_event_ids = [
    "PTAwMDAwMzY3MjM90",  # 2024 NIT
    "PTAwMDAwMzM4MDQ90",  # 2024 USAV 14-17
    "PTAwMDAwMzM4MDM90",  # 2024 USAV 11-13
    "PTAwMDAwMzY0NDM90", #2024 AAU Wave 4
    "PTAwMDAwMzY0NDE90", #2024 AAU Wave 3
    "PTAwMDAwMzY0NDA90", #2024 AAU Wave 2
    "PTAwMDAwMzYzNzA90", #2024 AAU Wave 1
    # Add more event IDs here
]

# Sportwrench Event URLs
sw_event_urls = [
    "https://events.sportwrench.com/#/events/6583cabd2",
    "https://events.sportwrench.com/#/events/abbfb1d13",
    "https://events.sportwrench.com/#/events/870cf0151",
    "https://events.sportwrench.com/#/events/7ccb7d73a",
    "https://events.sportwrench.com/#/events/aac1370ff",
    "https://events.sportwrench.com/#/events/e73a9d3b3",
    "https://events.sportwrench.com/#/events/c098ff439"
]

# Initialize an empty DataFrame to hold all data
aes_all_data = pd.DataFrame()
sportwrench_data = pd.DataFrame()
jacker_teams = pd.DataFrame()
jacker_eventID = 10526  # Set to ID of event in Jacker
# Set to True if you want to filter only by teams in the Jacker event listed above
jacker_filter = True

# Function to increment TeamCode


def increment_team_code(team_code):
    import re
    match = re.search(r"g(\d+)(.+)", team_code)
    if match:
        number = int(match.group(1)) + 1  # Increment the numeric portion
        return f"g{number}{match.group(2)}"
    return team_code  # Return the original if no match

# Function to fetch and process event data


def process_event(event_id, increment_code=False):
    print(f"Processing event ID: {event_id}")

    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch event details for event ID: {
              event_id}. Status code: {response.status_code}")
        return pd.DataFrame()

    event_data = response.json()
    event_name = event_data.get("Name", f"Event_{event_id}")
    print(f"Processing {event_name}")

    # Get all division IDs for this event
    division_ids = [division["DivisionId"]
                    for division in event_data.get("Divisions", [])]

    # Fetch standings for each division
    teams = []
    for division_id in division_ids:
        standings_url = f"https://results.advancedeventsystems.com/odata/{event_id}/standings(dId={
            division_id},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
        response = requests.get(standings_url)
        if response.status_code == 200:
            standings_data = response.json()
            teams.extend([
                {
                    "TeamName": team["TeamName"],
                    "TeamCode": increment_team_code(team["TeamCode"]) if increment_code else team["TeamCode"],
                    "OriginalTeamCode": team["TeamCode"],
                    "FinishRank": f"{team['FinishRank']} ({team['Division']['Name']})",
                    "DivisionName": team["Division"]["Name"],
                    "EventName": event_name,
                }
                for team in standings_data.get("value", [])
            ])
        else:
            print(f"Failed to fetch standings for division ID: {
                  division_id}. Status code: {response.status_code}")
    return pd.DataFrame(teams)


def pull_jacker_teams(jacker_id):
    """
    Fetches team data from the API based on the given jacker_id,
    adds a '2025NIT' column, creates a pivot table with 'TeamCode' as the index.

    Args:
        jacker_id (int): The ID to fetch data from the API.

    Returns:
        pd.DataFrame: The pivot table as a pandas DataFrame.
    """
    # API endpoint
    url = f"https://www.triplecrownsports.com/Data/UAGetTeams/?id={jacker_id}"

    # Fetch data from the API
    response = requests.get(url)

    if response.status_code == 200:
        # Parse JSON response
        data = response.json()

        # Convert JSON data to a pandas DataFrame
        df = pd.DataFrame(data)

        # Convert TeamCode to lowercase
        df["TeamCode"] = df["TeamCode"].str.lower()

        # Add the 2025NIT column with "Yes" for all rows
        df["2025NIT"] = "Yes"

        # Create a pivot table with TeamCode as the index
        pivot_table = df.pivot_table(
            index="TeamCode",
            values="2025NIT",
            aggfunc="first"  # Ensures the column remains "Yes"
        ).reset_index()

        print(f"Pulled data from 2025 NIT")
        return pivot_table
    else:
        print(f"Failed to fetch data from the API. Status code: {
              response.status_code}")
        return None


# Process first list of event IDs
for event_id in event_ids:
    aes_all_data = pd.concat(
        [aes_all_data, process_event(event_id)], ignore_index=True)

# Process second list of event IDs with TeamCode increment
for event_id in increment_teamcode_event_ids:
    aes_all_data = pd.concat([aes_all_data, process_event(
        event_id, increment_code=True)], ignore_index=True)


# Start Sportwrench results scraping
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
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a[href*='/divisions/']")))

        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/divisions/']")
        divisions = []
        for link in links:
            href = link.get_attribute("href")
            match = re.search(r"/divisions/(\d+)$", href)
            if match:
                division_id = match.group(1)
                division_name = link.text.strip()
                divisions.append({"Division ID": division_id,
                                 "Division Name": division_name})

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
        standings_url = f"https://events.sportwrench.com/#/events/{
            event_id}/divisions/{division_id}/standings"
        driver.get(standings_url)

        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".standings-team-name")))

        rows = driver.find_elements(By.CSS_SELECTOR, "table tr")[
            1:]  # Skip the header row

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
        wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "esw_title")))

        event_name = driver.find_element(
            By.CLASS_NAME, "esw_title").text.strip()
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
            print(f"Invalid event URL format for {
                  url}. Unable to extract event ID.")
            continue
        event_id = match.group(1)

        for division in divisions:
            division_id = division["Division ID"]
            division_name = division["Division Name"]
            print(f"Fetching standings for division: {
                  division_name} (ID: {division_id}) in event {event_name}")
            standings = extract_standings(
                event_id, division_id, division_name, event_name)
            if standings:
                all_data.extend(standings)
            else:
                print(f"No standings found for Division {
                      division_name} (ID: {division_id}) in event {event_name}")

    # Combine all standings into a DataFrame
    df = pd.DataFrame(all_data)
    if df.empty:
        print("No standings data collected across events.")
        return

    df.rename(columns={'Code': 'TeamCode'}, inplace=True)
    df.rename(columns={'Finish': 'FinishRank'}, inplace=True)
    df.rename(columns={'Event Name': 'EventName'}, inplace=True)
    df.rename(columns={'Team Name': 'TeamName'}, inplace=True)
    df.rename(columns={'Division Name': 'DivisionName'}, inplace=True)
    df.drop(columns=["Division ID"])
    df.drop(columns=["TeamName"])

    # return pivoted_df
    return df


# Scrape Sportwrench data
sportwrench_data = process_multiple_events(sw_event_urls)

# Combine Sportwrench and AES data
aes_all_data = pd.concat(
    [aes_all_data, sportwrench_data], ignore_index=True)
aes_all_data.to_csv("raw_nonpivoted_data.csv", index=False)

# Pivot the data to group by TeamCode and include columns for each event Name
pivot_data = aes_all_data.pivot_table(
    index="TeamCode",
    columns="EventName",
    values="FinishRank",
    aggfunc="first"
).reset_index()

# Pull list of team names from events
team_names = aes_all_data.groupby("OriginalTeamCode")[
    "TeamName"].first().reset_index()
team_names.rename(columns={'OriginalTeamCode': 'TeamCode'}, inplace=True)

# Add the TeamName as the first column
pivot_data = pd.merge(team_names, pivot_data, on="TeamCode")
pivot_data.to_csv("nonfiltered_all_event_standings.csv", index=False)

# Pull team codes from Jacker for 2025 NIT
if jacker_filter == True:
    jacker_teams = pull_jacker_teams(jacker_eventID)

    # Merge on TeamCode field to filter data by teams in Jacker event
    pivot_data = pd.merge(jacker_teams, pivot_data, on="TeamCode")

# Save the consolidated data to a single CSV file
csv_file_path = "combined_years_all_event_standings.csv"
pivot_data.to_csv(csv_file_path, index=False)
print(f"Consolidated standings saved to {csv_file_path}")