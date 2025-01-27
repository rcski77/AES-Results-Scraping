import requests
import pandas as pd

# List of event IDs to process
event_ids = [
    "PTAwMDAwMzY3MjM90", #2024 NIT
    "PTAwMDAwMzM4MDQ90", #2024 USAV
    "PTAwMDAwMzM4MDM90", 
    "PTAwMDAwMzI5MDM90", #2024 AAU
    "PTAwMDAwMzI5MDI90",
    "PTAwMDAwMzI5MDE90",
    "PTAwMDAwMzI4OTk90",
    # "PTAwMDAwMzcwNTU90", #2025 MLK 3 Step
    # "PTAwMDAwMzY5NDk90",
    # "PTAwMDAwMzY3NDY90",
    # "PTAwMDAwMzg4Mzk90",
    # "PTAwMDAwMzczMjU90",
    # "PTAwMDAwMzczMjY90",
    # "PTAwMDAwMzcwODk90",
    # "PTAwMDAwMzY5MTI90"
    ]  # Add your event IDs here

# Initialize an empty DataFrame to hold all data
all_data = pd.DataFrame()

# Dictionary to map event IDs to their Names
event_id_to_name = {}

# Iterate over each event ID
for event_id in event_ids:
    #print(f"Processing event ID: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    
    # Fetch event details
    response = requests.get(base_url)
    if response.status_code == 200:
        event_data = response.json()
        
        # Extract the event Name and map it to the eventID
        event_name = event_data.get("Name", f"Event_{event_id}")
        event_id_to_name[event_id] = event_name
        
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
    index=["TeamCode", "TeamName"], 
    columns="EventName", 
    values="FinishRank", 
    aggfunc="first"
).reset_index()

# Save the consolidated data to a single CSV file
csv_file_path = "all_event_standings_by_name.csv"
pivot_data.to_csv(csv_file_path, index=False)
print(f"Consolidated standings saved to {csv_file_path}")
