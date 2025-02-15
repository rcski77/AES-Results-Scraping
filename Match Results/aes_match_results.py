import re
import requests
import pandas as pd
import streamlit as st


# First list of event IDs to process normally - current year's events
aes_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzg4Mzk90",  # CO Challenge
    # Add more event IDs here
]

# Initialize an empty DataFrame to hold all data
aes_all_data = pd.DataFrame()
aes_match_results = pd.DataFrame()

# Streamlit App Title
st.title("Volleyball Match Results")

# Function to fetch and process event data
def process_event(url, increment_code=False):
    
    global aes_match_results
    
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
                    "TeamCode": team["TeamCode"],
                    "OriginalTeamCode": team["TeamCode"],
                    "AESTeamID": team["TeamId"],
                    "FinishRank": f"{team['FinishRank']} ({team['Division']['Name']})",
                    "DivisionName": team["Division"]["Name"],
                    "DivisionID" : team["Division"]["DivisionId"],
                    "EventName": event_name,
                }
                for team in standings_data.get("value", [])
            ])
        else:
            print(f"Failed to fetch standings for division ID: {
                  division_id}. Status code: {response.status_code}")
        
    results = process_match_results(teams, event_id)
    
    aes_match_results = pd.concat(
        [aes_match_results, results], ignore_index=True)
    
    return pd.DataFrame(teams)
        

# Process match results
def process_match_results(team_list, event_id):
    match_list = []
    
    for team in team_list:
        aes_teamID = team["AESTeamID"]
        division_id = team["DivisionID"]
        base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}/division/{division_id}/team/{aes_teamID}/schedule/past"
        
        response = requests.get(base_url)
        if response.status_code != 200:
            print(f"Failed to fetch event details for event ID: {
                event_id}. Status code: {response.status_code}")
            return pd.DataFrame()
        
        data = response.json()
        
        # Iterate through matches and extract details
        for match_data in data:
            match = match_data["Match"]
            
            match_id = match["MatchId"]
            
            first_team_id = match["FirstTeamId"]
            first_team_name = match["FirstTeamName"]
            first_team_won = match["FirstTeamWon"]
            
            second_team_id = match["SecondTeamId"]
            second_team_name = match["SecondTeamName"]
            
            # Extract set scores
            set_scores = [set_data["ScoreText"] for set_data in match["Sets"] if set_data["ScoreText"]]

            # Determine match result
            winner = first_team_name if first_team_won else second_team_name
                
            match_list.append({
                "Match ID": match_id,
                "First Team ID": first_team_id,
                "First Team Name": first_team_name,
                "Second Team ID": second_team_id,
                "Second Team Name": second_team_name,
                "Winner": winner,
                "Set Scores": ", ".join(set_scores)
            })
            
    # Convert list to DataFrame
    df = pd.DataFrame(match_list)
    
    # Remove duplicates based on Match ID
    df = df.drop_duplicates(subset=["Match ID"], keep="first")

    # # Export DataFrame to CSV
    # df.to_csv("match_results.csv", index=False)
    
    return df
    
    
# Process first list of event IDs
for url in aes_urls:
    aes_all_data = pd.concat(
        [aes_all_data, process_event(url)], ignore_index=True)
    
all_teams = sorted(set(aes_match_results["First Team Name"]).union(set(aes_match_results["Second Team Name"])))
    
# Dropdown to select a team
selected_team = st.selectbox("Select a Team to Filter Matches", ["All Teams"] + all_teams)

# Filter the DataFrame based on the selected team
if selected_team != "All Teams":
    aes_match_results = aes_match_results[(aes_match_results["First Team Name"] == selected_team) | (aes_match_results["Second Team Name"] == selected_team)]

# print("Data successfully saved to match_results.csv")
# Display DataFrame in Streamlit
st.subheader("Match Results")
st.dataframe(aes_match_results)