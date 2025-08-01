import requests
import json
import pandas as pd
import re

# List of event URLs to process
event_urls = [
    "https://vbschedule.com/app/results/event/97/divisions",
    "https://vbschedule.com/app/results/event/98/divisions",
    "https://vbschedule.com/app/results/event/99/divisions",
    # Add more URLs here as needed
]

def process_event(event_url):
    # Extract event ID from URL
    match = re.search(r'/event/(\d+)/', event_url)
    if not match:
        print(f"Could not extract event ID from URL: {event_url}")
        return
    
    event_id = match.group(1)
    print(f"\nProcessing event ID: {event_id}")
    
    # API endpoint for event details
    api_url = f"https://api.vbschedule.com/results/event/{event_id}"
    
    # Make the API call
    response = requests.get(api_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch event data for event ID: {event_id}. Status code: {response.status_code}")
        return
    if response.status_code != 200:
        print(f"Failed to fetch event data for event ID: {event_id}. Status code: {response.status_code}")
        return
    
    data = response.json()
    
    # Get event details for filename
    event_info = data.get("event", {})
    event_name = event_info.get("name", f"Event_{event_id}")
    event_dates = event_info.get("event_dates", [])
    event_date = event_dates[0] if event_dates else "Unknown_Date"
    
    print(f"Processing: {event_name}")
    
    # Extract division IDs from the eventDivisions array
    division_ids = []
    division_names = {}
    event_divisions = data.get("event", {}).get("eventDivisions", [])
    
    print("Division IDs and Names:")
    for division in event_divisions:
        division_id = division.get("id")
        division_name = division.get("name")
        division_ids.append(division_id)
        division_names[division_id] = division_name
        print(f"ID: {division_id} - Name: {division_name}")
    
    print(f"Total divisions found: {len(division_ids)}")
    
    # Now fetch teams for each division
    all_teams = []
    
    for division_id in division_ids:
        teams_url = f"https://api.vbschedule.com/results/event-division/{division_id}/teams"
        print(f"Fetching teams for division {division_id} ({division_names[division_id]})...")
        
        teams_response = requests.get(teams_url)
        if teams_response.status_code == 200:
            teams_data = teams_response.json()
            teams = teams_data.get("teams", [])
            
            for team in teams:
                alternate_id = team.get("alternate_identifier")
                final_finish = team.get("final_finish")
                
                # Skip teams without alternate_identifier or final_finish
                if not alternate_id or final_finish is None:
                    continue
                    
                all_teams.append({
                    "DivisionName": division_names[division_id],
                    "FinalFinish": final_finish,
                    "TeamName": team.get("name"),
                    "AlternateIdentifier": alternate_id.lower()
                })
            
            print(f"Found {len(teams)} teams in {division_names[division_id]}")
        else:
            print(f"Failed to fetch teams for division {division_id}. Status code: {teams_response.status_code}")
    
    # Create DataFrame
    teams_df = pd.DataFrame(all_teams)
    
    # Sort by division name first, then by final finish
    teams_df = teams_df.sort_values(['DivisionName', 'FinalFinish'])
    
    print(f"Total teams found: {len(teams_df)}")
    print("First 10 teams:")
    print(teams_df.head(10))
    
    # Create filename with event date and sanitized event name
    event_name_sanitized = re.sub(r'[<>:"/\\|?*]', '', event_name)  # Remove invalid characters
    filename = f'US Club Rankings\\data\\{event_date}_{event_name_sanitized}_teams.csv'
    
    # Save to CSV without headers
    teams_df.to_csv(filename, index=False, header=False)
    print(f"Data saved to {filename}")

# Process all events
for event_url in event_urls:
    process_event(event_url)