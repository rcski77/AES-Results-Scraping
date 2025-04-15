import requests
import pandas as pd
import re

# List of event URLs to process for US Club Rankings import
event_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwNDU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NDY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcyMDY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcxNDE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY4OTc90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY4OTY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcxNDM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcyMDk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgyODA90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMDc90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzk1NDE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzk1NDI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NDk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NTU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY3NDY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc3Mjk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzg0NTc90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc0NDc90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMDM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY4MzQ90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcyODk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzg0Nzc90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc5Njk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcxNDI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5MTI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzczMTg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc1Njk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwNTU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY4ODk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwMDU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzg3MjI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc0Mzk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc0OTU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc1ODg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc3MzI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMDg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwMzM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwOTE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwODY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzg4Mzk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NDg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NTk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NjI90",
]

# Initialize an empty DataFrame to hold all data
all_data = pd.DataFrame()

# Function to fetch and process event data
def process_event(event_url, increment_code=False):
    match = re.search(r'/event/([^/]+)$', event_url)
    event_id = match.group(1) if match else None
    
    print(f"Processing event ID: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")
        return
    
    event_data = response.json()
    event_name = event_data.get("Name", f"Event_{event_id}")
    event_date = event_data.get("StartDate", "Unknown Date").split("T")[0]
    print(f"Processing {event_name}")
    
    # Get all division IDs for this event
    division_ids = [division["DivisionId"] for division in event_data.get("Divisions", [])]
    
    # Fetch standings for each division
    teams = []
    for division_id in division_ids:
        standings_url = f"https://results.advancedeventsystems.com/odata/{event_id}/standings(dId={division_id},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
        response = requests.get(standings_url)
        if response.status_code == 200:
            standings_data = response.json()
            teams.extend([
                {
                    "DivisionName": team["Division"]["Name"],
                    "FinishRank": f"{team['FinishRank']}",
                    "TeamName": team["TeamText"],
                    "TeamCode": team["TeamCode"],
                }
                for team in standings_data.get("value", [])
            ])
        else:
            print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
            
    event_data = pd.DataFrame(teams)
    event_name_sanitized = re.sub(r'[<>:"/\\|?*]', '', event_name)  # Remove invalid characters
    event_data.to_csv(f'US Club Rankings\data\{event_date}_{event_name_sanitized}_{event_id}_standings.csv', index=False, header=False)

# Process first list of event IDs
for event_url in event_urls:
    process_event(event_url)