from scrapling import StealthyFetcher
import pandas as pd
from bs4 import BeautifulSoup
import json
import re

fetcher = StealthyFetcher(auto_match=False)
sportwrench_data = pd.DataFrame()

# Sportwrench Event URLs
sw_event_urls = [
    "https://events.sportwrench.com/#/events/e1a3a70be",
    "https://events.sportwrench.com/#/events/1324af385",
    "https://events.sportwrench.com/#/events/9e6d38cfc",
    "https://events.sportwrench.com/#/events/e47af10c0"
]


def process_event(url):
    df = pd.DataFrame() # create empty dataframe for each event
    event_id = url.rsplit("/", 1)[-1]
    
    # Define the base API endpoint for the event 
    base_url = f"https://events.sportwrench.com/api/esw/{event_id}"
    
    page = fetcher.fetch(base_url)
    if (page.status != 200):
        print(f"Failed to fetch event details for event ID: {
              event_id}. Status code: {page.status}")
        return pd.DataFrame()

    soup = BeautifulSoup(page.html_content, "html.parser")
    json_text = soup.find("pre").text
    
    try:
        data = json.loads(json_text)  # this converts the text into a Python dict
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        return pd.DataFrame()

    event_name = data.get('long_name')
    event_date = data.get('date_start').replace("/", "-")
    print(f"Processing {event_name} / ID: {event_id}")
    
    #Get all divisions and IDs for event
    division_url = f"https://events.sportwrench.com/api/esw/{event_id}/divisions"
    div_page = fetcher.fetch(division_url)
    if (div_page.status == 200):
        div_soup = BeautifulSoup(div_page.html_content, "html.parser")
        json_text = div_soup.find("pre").text
        try:
            div_data = json.loads(json_text) 
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return pd.DataFrame()
        
        division_ids = [division["division_id"] for division in div_data]
        
        for division_id in division_ids:
            standings_url =f"https://events.sportwrench.com/api/esw/{event_id}/divisions/{division_id}/standings"
            standings_page = fetcher.fetch(standings_url)
            if (standings_page.status == 200):
                standings_soup = BeautifulSoup(standings_page.html_content, "html.parser")
                json_text = standings_soup.find("pre").text
                try:
                    standings_data = json.loads(json_text) 
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    return pd.DataFrame()
                
                # Extract data into a list
                teams_list = []
                for division, teams in standings_data["teams"].items():
                    for team in teams:
                        teams_list.append({
                            "Division": team["division_name"],
                            "Seed": team["seed_current"],
                            "Team Name": team["team_name"],
                            "Team Code": team["organization_code"].lower(),
                         })
                df = pd.concat([df, pd.DataFrame(teams_list)], ignore_index=True)
    
    event_name_sanitized = re.sub(r'[<>:"/\\|?*]', '', event_name)  # Remove invalid characters
    df.to_csv(f'US Club Rankings\data\{event_date}_{event_name_sanitized}_{event_id}_standings.csv', index=False, header=False)


# Process URLs in Sportwrench list    
for url in sw_event_urls:
    process_event(url)