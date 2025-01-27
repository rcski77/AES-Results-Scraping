import requests
import pandas as pd

# Define the base API endpoint
base_url = "https://results.advancedeventsystems.com/api/event/{eventID}"

# Specify the event ID as a variable
event_id = "PTAwMDAwMzM4MDQ90"  # Replace with the desired event ID

# Format the URL with the event ID
url = base_url.format(eventID=event_id)

# Headers for the request
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store, no-cache",
}

# Send a GET request to fetch event details
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    json_data = response.json()
    
    # Get an array of all division IDs    
    division_ids = [division["DivisionId"] for division in json_data.get("Divisions", [])]
    
    # Initialize an empty list to collect all team standings across divisions
    all_teams = []
    
    # Iterate through all division IDs
    for division_id in division_ids:
        standings_url = "https://results.advancedeventsystems.com/odata/{eventID}/standings(dId={divisionID},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
        url = standings_url.format(eventID=event_id, divisionID=division_id)
        
        # Send the GET request for standings
        response = requests.get(url)
        
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract relevant fields from the standings
            for team in data["value"]:
                all_teams.append({
                    "TeamName": team["TeamName"],
                    "TeamCode": team["TeamCode"],
                    "FinishRank": team["FinishRank"],
                    "DivisionName": team["Division"]["Name"],
                })
        else:
            print(f"Failed to fetch data for Division ID {division_id}. Status code: {response.status_code}")
    
    # Create a pandas DataFrame with all teams
    df = pd.DataFrame(all_teams)
    
    # Save all standings grouped by TeamCode into one CSV file
    csv_file_path = "all_team_standings.csv"
    df.to_csv(csv_file_path, index=False)
    print(f"All standings saved to {csv_file_path}")

else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
