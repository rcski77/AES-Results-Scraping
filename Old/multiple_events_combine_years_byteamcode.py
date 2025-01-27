import requests
import pandas as pd

# First list of event IDs to process normally - current year's events
event_ids = [
    "PTAwMDAwMzY3NDY90", # Central Zone
    "PTAwMDAwMzg4Mzk90", # CO Challenge
    "PTAwMDAwMzcwNTU90", #2025 MLK 3 Step
    "PTAwMDAwMzY5NDk90",
    "PTAwMDAwMzczMjU90",
    "PTAwMDAwMzczMjY90",
    "PTAwMDAwMzcwODk90",
    "PTAwMDAwMzY5MTI90"
    # Add more event IDs here
]

# Second list of event IDs where TeamCodes will be incremented - last year's events
increment_teamcode_event_ids = [
   "PTAwMDAwMzY3MjM90", #2024 NIT
    "PTAwMDAwMzM4MDQ90", #2024 USAV 14-17
    "PTAwMDAwMzM4MDM90", #2024 USAV 11-13
    "PTAwMDAwMzI5MDM90", #2024 AAU Wave 4
    "PTAwMDAwMzI5MDI90", #2024 AAU Wave 3
    "PTAwMDAwMzI5MDE90", #2024 AAU Wave 2
    "PTAwMDAwMzI4OTk90", #2024 AAU Wave 1
    # Add more event IDs here
]

# Initialize an empty DataFrame to hold all data
all_data = pd.DataFrame()

# Dictionary to map event IDs to their Names
event_id_to_name = {}

# Function to increment TeamCode
def increment_team_code(team_code):
    # Find the numeric portion of the team code and increment it by 1
    import re
    match = re.search(r"g(\d+)(.+)", team_code)
    if match:
        number = int(match.group(1)) + 1  # Increment the numeric portion
        return f"g{number}{match.group(2)}"
    return team_code  # Return the original if no match

# Process first list of event IDs
for event_id in event_ids:
    print(f"Processing event ID: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    
    # Fetch event details
    response = requests.get(base_url)
    if response.status_code == 200:
        event_data = response.json()
        
        # Extract the event Name and map it to the eventID
        event_name = event_data.get("Name", f"Event_{event_id}")
        event_id_to_name[event_id] = event_name
        print(f"Processing {event_name}")
        
        # Get all division IDs for this event
        division_ids = [division["DivisionId"] for division in event_data.get("Divisions", [])]
        
        # Process standings for each division
        for division_id in division_ids:
            #print(f"Fetching standings for division ID: {division_id}")
            
            standings_url = f"https://results.advancedeventsystems.com/odata/{event_id}/standings(dId={division_id},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
            response = requests.get(standings_url)
            
            if response.status_code == 200:
                standings_data = response.json()
                
                # Extract relevant fields and include event Name as a column
                teams = [
                    {
                        "TeamName": team["TeamName"],
                        "TeamCode": team["TeamCode"],
                        "OriginalTeamCode": team["TeamCode"],
                        "FinishRank": f"{team['FinishRank']} ({team['Division']['Name']})",  # Add division name with rank
                        "DivisionName": team["Division"]["Name"],
                        "EventName": event_name,  # Use event Name instead of event ID
                    }
                    for team in standings_data.get("value", [])
                ]
                
                # Append the data to a DataFrame
                all_data = pd.concat([all_data, pd.DataFrame(teams)], ignore_index=True)
            else:
                print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
    else:
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")

# Process second list of event IDs
for event_id in increment_teamcode_event_ids:
    print(f"Processing event ID with TeamCode increment: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    
    # Fetch event details
    response = requests.get(base_url)
    if response.status_code == 200:
        event_data = response.json()
        
        # Extract the event Name and map it to the eventID
        event_name = event_data.get("Name", f"Event_{event_id}")
        event_id_to_name[event_id] = event_name
        print(f"Processing {event_name}")
        
        # Get all division IDs for this event
        division_ids = [division["DivisionId"] for division in event_data.get("Divisions", [])]
        
        # Process standings for each division
        for division_id in division_ids:
            #print(f"Fetching standings for division ID: {division_id}")
            
            standings_url = f"https://results.advancedeventsystems.com/odata/{event_id}/standings(dId={division_id},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
            response = requests.get(standings_url)
            
            if response.status_code == 200:
                standings_data = response.json()
                
                # Extract relevant fields, increment TeamCode, and include event Name
                teams = [
                    {
                        "TeamName": team["TeamName"],
                        "TeamCode": increment_team_code(team["TeamCode"]),  # Increment TeamCode
                        "OriginalTeamCode": team["TeamCode"],
                        "FinishRank": f"{team['FinishRank']} ({team['Division']['Name']})",  # Add division name with rank
                        "DivisionName": team["Division"]["Name"],
                        "EventName": event_name,  # Use event Name instead of event ID
                    }
                    for team in standings_data.get("value", [])
                ]
                
                # Append the data to a DataFrame
                all_data = pd.concat([all_data, pd.DataFrame(teams)], ignore_index=True)
            else:
                print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
    else:
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")

# Pivot the data to group by TeamCode and include columns for each event Name
pivot_data = all_data.pivot_table(
    index="TeamCode", 
    columns="EventName", 
    values="FinishRank", 
    aggfunc="first"
).reset_index()

# Pull list of team names from events
team_names = all_data.groupby("OriginalTeamCode")["TeamName"].first().reset_index()
team_names.rename(columns={'OriginalTeamCode':'TeamCode'}, inplace=True)

# Add the TeamName as the first column
pivot_data = pd.merge(team_names, pivot_data, on="TeamCode")

# Save the consolidated data to a single CSV file
csv_file_path = "combined_years_all_event_standings.csv"
pivot_data.to_csv(csv_file_path, index=False)
print(f"Consolidated standings saved to {csv_file_path}")