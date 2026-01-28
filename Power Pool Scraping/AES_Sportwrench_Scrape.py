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
aes_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDIzODM90",  # Tropical Ice
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDE0MjM90",  # Tour TX 1 Austin
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDI3ODA90",  # CO Challenge
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDEzMTc90", # JVA Rock N Rumble Wk1
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDEzMTg90", # JVA Rock N Rumble Wk2
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDIyMzE90", # ASICS MLK Kansas City
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDEyMDM90",  # 25 MEPL
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDA5MDc90",  # Nike Classic
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDE0MTg90",  # Fiesta MLK AZ
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDEwMDc90", # Windy City 18s Qualifier
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDEwMDQ90",  # City of Oaks
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDIzMjg90", # SLC Showdown 18s
    # "https://results.advancedeventsystems.com/event/PTAwMDAwNDA4ODE90", # Central Zone - don't use
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDE1NDE90", # Lonestar 18s Qualifier
    # Add more event IDs here
]

# Second list of event IDs where TeamCodes will be incremented - last year's events
aes_prev_year_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgzNjE90",  # 2025 NIT
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc4OTU90",  # 2025 USAV 14-17
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc4MjM90",  # 2025 USAV 11-13
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTI90",  # 2025 AAU Wave 4
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTE90",  # 2025 AAU Wave 3
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTA90",  # 2025 AAU Wave 2
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMDk90",  # 2025 AAU Wave 1
    # Add more event IDs here
]

# Sportwrench Event URLs
sw_event_urls = [
    # "https://events.sportwrench.com/#/events/c268be348",  # SCVA Power League 18s
    # "https://events.sportwrench.com/#/events/902b84069",  # SCVA Power League 13s
    # "https://events.sportwrench.com/#/events/cda491982",  # SCVA Power League 14s
    # "https://events.sportwrench.com/#/events/5c8c9cb5a",  # SCVA Power League 15s
    # "https://events.sportwrench.com/#/events/19564617e",  # SCVA Power League 16s
    # "https://events.sportwrench.com/#/events/a7f82c80a",  # SCVA Power League 17s/12s
    # "https://events.sportwrench.com/#/events/9a1567895", # SCVA Power Leagues 14s Week 2
    # "https://events.sportwrench.com/#/events/6ff9c1e1b", #Florida Fest Qualifier
]

# Initialize an empty DataFrame to hold all data
combined_aes_sw_all_data = pd.DataFrame()
sportwrench_data = pd.DataFrame()
jacker_teams = pd.DataFrame()
# Path to CSV file with NIT team codes
nit_csv_path = "Power Pool Scraping/NIT_team_codes.csv"
# Path to CSV file with jotform status
jotforms_csv_path = "Power Pool Scraping/NIT_jotforms.csv"
# Path to CSV file with team code conversions for teams that changed codes
team_code_conversions_path = "Power Pool Scraping/team_code_conversions.csv"
jacker_filter = True  # Set to True if you want to filter only by teams in the CSV file

# Load team code conversions
team_code_mapping = {}
try:
    conversions_df = pd.read_csv(team_code_conversions_path)
    # Create a mapping from LastCode to CurrentCode (all lowercase)
    team_code_mapping = dict(zip(conversions_df['LastCode'].str.lower(), 
                                 conversions_df['CurrentCode'].str.lower()))
    print(f"Loaded {len(team_code_mapping)} team code conversions from {team_code_conversions_path}")
except FileNotFoundError:
    print(f"Team code conversions CSV not found: {team_code_conversions_path}. Proceeding without conversions.")
except Exception as e:
    print(f"Error reading team code conversions CSV: {e}. Proceeding without conversions.")


# Function to increment TeamCode or use conversion mapping
def increment_team_code(team_code):
    import re
    # First check if this team code has a conversion mapping
    team_code_lower = team_code.lower()
    if team_code_lower in team_code_mapping:
        return team_code_mapping[team_code_lower]
    
    # Otherwise, use the default increment logic
    match = re.search(r"g(\d+)(.+)", team_code)
    if match:
        number = int(match.group(1)) + 1  # Increment the numeric portion
        return f"g{number}{match.group(2)}"
    return team_code  # Return the original if no match


# Function to fetch and process event data
def process_aes_event(url, increment_code=False):

    match = re.search(r'/event/([^/]+)$', url)
    event_id = match.group(1) if match else None

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


def pull_jacker_teams(csv_file_path):
    """
    Reads team codes from a CSV file containing NIT team codes,
    adds a '2026NIT' column, and creates a DataFrame for filtering.

    Args:
        csv_file_path (str): Path to the CSV file containing team codes.

    Returns:
        pd.DataFrame: DataFrame with TeamCode, Team Name, and 2026NIT columns.
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)

        # Convert TeamCode to lowercase
        df["Team Code"] = df["Team Code"].str.lower()

        # Rename the columns to TeamCode and TeamName for consistency
        df.rename(columns={"Team Code": "TeamCode",
                  "Team Name": "TeamName"}, inplace=True)

        # Add the 2026NIT column with "Yes" for all rows
        df["2026NIT"] = "Yes"

        # Keep TeamCode, TeamName, and 2026NIT columns
        df = df[["TeamCode", "TeamName", "2026NIT"]]

        print(f"Loaded {len(df)} team codes from {csv_file_path}")
        return df
    except FileNotFoundError:
        print(f"CSV file not found: {csv_file_path}")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


# Process first list of event IDs
for url in aes_urls:
    combined_aes_sw_all_data = pd.concat(
        [combined_aes_sw_all_data, process_aes_event(url)], ignore_index=True)

# Process second list of event IDs with TeamCode increment
for url in aes_prev_year_urls:
    combined_aes_sw_all_data = pd.concat([combined_aes_sw_all_data, process_aes_event(
        url, increment_code=True)], ignore_index=True)


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


def process_sw_events(urls):
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
sportwrench_data = process_sw_events(sw_event_urls)

# Combine Sportwrench and AES data
combined_aes_sw_all_data = pd.concat(
    [combined_aes_sw_all_data, sportwrench_data], ignore_index=True)
combined_aes_sw_all_data.to_csv("Power Pool Scraping/data/raw_nonpivoted_data.csv", index=False)

# Pivot the data to group by TeamCode and include columns for each event Name
pivot_data = combined_aes_sw_all_data.pivot_table(
    index="TeamCode",
    columns="EventName",
    values="FinishRank",
    aggfunc="first"
).reset_index()

# Pull list of team names from events
team_names = combined_aes_sw_all_data.groupby("OriginalTeamCode")[
    "TeamName"].first().reset_index()
team_names.rename(columns={'OriginalTeamCode': 'TeamCode'}, inplace=True)

# Add TeamName from scraped data without dropping teams missing a name
pivot_data = pd.merge(pivot_data, team_names, on="TeamCode", how="left")
pivot_data.to_csv(
    "Power Pool Scraping/data/nonfiltered_all_event_standings.csv", index=False)

# Pull team codes from CSV for 2026 NIT
if jacker_filter == True:
    jacker_teams = pull_jacker_teams(nit_csv_path)

    # Merge on TeamCode field - use right join to include all NIT teams even without results
    if jacker_teams is not None:
        pivot_data = pd.merge(pivot_data, jacker_teams,
                              on="TeamCode", how="right")
        # Use TeamName from NIT CSV (TeamName_y) and drop the scraped TeamName (TeamName_x)
        pivot_data["TeamName"] = pivot_data["TeamName_y"].fillna(
            pivot_data["TeamName_x"])
        pivot_data.drop(columns=["TeamName_x", "TeamName_y"], inplace=True)
    else:
        print("Warning: Could not filter by NIT teams. Proceeding with all teams.")

# Load and merge jotform status data
try:
    jotforms_df = pd.read_csv(jotforms_csv_path)
    jotforms_df["Team Code"] = jotforms_df["Team Code"].str.lower()
    jotforms_df.rename(columns={"Team Code": "TeamCode"}, inplace=True)

    # Keep only TeamCode and Power Pool Jotform columns
    jotforms_df = jotforms_df[["TeamCode", "Power Pool Jotform"]]

    # Merge jotform data with pivot_data
    pivot_data = pd.merge(pivot_data, jotforms_df, on="TeamCode", how="left")

    # Fill empty values with "NO" - this handles both NaN and empty strings
    pivot_data["Power Pool Jotform"] = pivot_data["Power Pool Jotform"].fillna(
        "NO")
    pivot_data["Power Pool Jotform"] = pivot_data["Power Pool Jotform"].replace(
        "", "NO")

    print(
        f"Loaded jotform status for {len(jotforms_df)} teams from {jotforms_csv_path}")
except FileNotFoundError:
    print(
        f"Jotform CSV file not found: {jotforms_csv_path}. Skipping jotform status.")
except Exception as e:
    print(f"Error reading jotform CSV file: {e}. Skipping jotform status.")

# Reorder columns: TeamCode, TeamName, 2026NIT, Power Pool Jotform, then all event columns
event_columns = [col for col in pivot_data.columns if col not in [
    "TeamCode", "TeamName", "Power Pool Jotform", "2026NIT"]]
column_order = ["TeamCode", "TeamName", "2026NIT", "Power Pool Jotform"] + event_columns
pivot_data = pivot_data[column_order]

# Save the consolidated data to a single CSV file
csv_file_path = "Power Pool Scraping/data/combined_years_all_event_standings.csv"
pivot_data.to_csv(csv_file_path, index=False)

print(f"Consolidated standings saved to {csv_file_path}")