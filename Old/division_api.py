import requests
import pandas as pd

# Define the base API endpoint
base_url = "https://results.advancedeventsystems.com/api/event/{eventID}"

# Specify the event ID as a variable
event_id = "PTAwMDAwMzM4MDQ90"  # Replace with the desired event ID

# Format the URL with the event ID
url = base_url.format(eventID=event_id)

# Optional: Add headers if required (e.g., authentication or content type)
headers = {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store, no-cache",
}

# Send a GET request to the API endpoint
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    json_data = response.json()
    
    # Process or display the data
    divisions = json_data.get("Divisions", [])
    
    # Get an array of all division IDs    
    division_ids = [division["DivisionId"] for division in json_data.get("Divisions", [])]
    
    # Iterate through array and save file of standings for each division
    for division_id in division_ids:
        standings_url = "https://results.advancedeventsystems.com/odata/{eventID}/standings(dId={divisionID},cId=null,tIds=[])?$orderby=OverallRank,FinishRank,TeamName,TeamCode"
        # Format the URL with event ID and division ID
        url = standings_url.format(eventID=event_id, divisionID=division_id)
        
        # Send the GET request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            #Save data to a CSV file
            teams = []
            division_name = None
            for team in data["value"]:
                teams.append({
                    "TeamName": team["TeamName"],
                    "TeamCode": team["TeamCode"],
                    "FinishRank": team["FinishRank"],
                    "DivisionName": team["Division"]["Name"],
                })
                division_name = team["Division"]["Name"]

            # Convert the extracted data to a pandas DataFrame
            df = pd.DataFrame(teams)
            
            # Format the division name for the file path (remove spaces and special characters)
            formatted_division_name = division_name.replace(" ", "_").replace("/", "_")

            # Save the DataFrame to a CSV file
            csv_file_path = f"team_standings_{formatted_division_name}.csv"  # Specify the desired file path
            df.to_csv(csv_file_path, index=False)
            
        else:
            print(f"Failed to fetch data for Division ID {division_id}. Status code: {response.status_code}")
        
else:
    print(f"Failed to fetch data. Status code: {response.status_code}")
