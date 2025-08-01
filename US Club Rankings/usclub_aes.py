import requests
import pandas as pd
import re

# List of event URLs to process for US Club Rankings import
event_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY3OTU90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwNDA90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY3OTY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY3OTM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5Njg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMzA90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwNDQ90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5Njk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMzI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMzg90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMjI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwNDM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzcwNDE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgwMzY90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NzA90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5NzE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMDk90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTA90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTE90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc4MjM90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDAzMTI90",
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzc4OTU90"
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
            if team.get("TeamCode") and str(team.get("TeamCode")).strip() not in ['', 'None', 'null']
            and team.get("FinishRank") != 'None'
            ])
        else:
            print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
            
    event_data = pd.DataFrame(teams)
    event_name_sanitized = re.sub(r'[<>:"/\\|?*]', '', event_name)  # Remove invalid characters
    max_rows = 400
    total_rows = len(event_data)
    
    if total_rows > max_rows:
        # Find division boundaries to avoid splitting divisions
        division_boundaries = []
        current_division = None
        
        for i, row in event_data.iterrows():
            if row['DivisionName'] != current_division:
                if current_division is not None:  # Not the first division
                    division_boundaries.append(i)
                current_division = row['DivisionName']
        
        # Add the end of the data as the final boundary
        division_boundaries.append(total_rows)
        
        # Create file splits respecting division boundaries
        file_num = 1
        start = 0
        
        for boundary in division_boundaries:
            # If adding this division would exceed max_rows, save current chunk
            if boundary - start > max_rows and start < boundary - 1:
                # Save what we have so far
                chunk = event_data.iloc[start:start + max_rows]
                # Find the last complete division in this chunk
                last_division = None
                split_point = start + max_rows
                
                for i in range(start + max_rows - 1, start - 1, -1):
                    if i < len(event_data):
                        current_div = event_data.iloc[i]['DivisionName']
                        if last_division is None:
                            last_division = current_div
                        elif current_div != last_division:
                            split_point = i + 1
                            break
                
                chunk = event_data.iloc[start:split_point]
                chunk.to_csv(
                    f'US Club Rankings\\data\\{event_date}_{event_name_sanitized}_{event_id}_standings_part{file_num}.csv',
                    index=False,
                    header=False
                )
                file_num += 1
                start = split_point
            
            # If we've reached the end or this is the last reasonable chunk
            if boundary == total_rows:
                if start < total_rows:
                    chunk = event_data.iloc[start:boundary]
                    chunk.to_csv(
                        f'US Club Rankings\\data\\{event_date}_{event_name_sanitized}_{event_id}_standings_part{file_num}.csv',
                        index=False,
                        header=False
                    )
    else:
        event_data.to_csv(
            f'US Club Rankings\\data\\{event_date}_{event_name_sanitized}_{event_id}_standings.csv',
            index=False,
            header=False
        )

# Process first list of event IDs
for event_url in event_urls:
    process_event(event_url)