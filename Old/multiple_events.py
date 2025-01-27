import requests
import pandas as pd

# List of event IDs to process
event_ids = ["PTAwMDAwMzM4MDQ90", "PTAwMDAwMzY3MjM90"]  # Add your event IDs here

# Initialize an empty DataFrame to hold all data
all_data = pd.DataFrame()

# Iterate over each event ID
for event_id in event_ids:
    print(f"Processing event ID: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    
    # Fetch event details
    response = requests.get(base_url)
    if response.status_code == 200:
        event_data = response.json()
        
        # Get all division IDs for this event
        division_ids = [division["DivisionId"] for division in event_data.get("Divisions", [])]
        
        # Process standings for each division
        for division_id in division_ids:
            print(f"Fetching standings for division ID: {division_id}")
            
            standings_url = f"https://results.advancedeventsystems.com/odata/{event_id}/standings(dId={division_id},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
            response = requests.get(standings_url)
            
            if response.status_code == 200:
                standings_data = response.json()
                
                # Extract relevant fields and include event ID as a column
                teams = [
                    {
                        "TeamName": team["TeamName"],
                        "TeamCode": team["TeamCode"],
                        "FinishRank": team["FinishRank"],
                        "DivisionName": team["Division"]["Name"],
                        "EventID": event_id,
                    }
                    for team in standings_data.get("value", [])
                ]
                
                # Append the data to a DataFrame
                all_data = pd.concat([all_data, pd.DataFrame(teams)], ignore_index=True)
            else:
                print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
    else:
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")

# Pivot the data to group by TeamCode and include columns for each event ID
pivot_data = all_data.pivot_table(
    index=["TeamCode", "TeamName"], 
    columns="EventID", 
    values="FinishRank", 
    aggfunc="first"
).reset_index()

# Save the consolidated data to a single CSV file
csv_file_path = "all_event_standings.csv"
pivot_data.to_csv(csv_file_path, index=False)
print(f"Consolidated standings saved to {csv_file_path}")
