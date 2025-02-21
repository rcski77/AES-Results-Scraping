import re
import requests
import pandas as pd
import streamlit as st

# First list of event IDs to process normally - current year's events
aes_urls = [
    # "https://results.advancedeventsystems.com/event/PTAwMDAwMzg4Mzk90",  # CO Challenge
    # "https://results.advancedeventsystems.com/event/PTAwMDAwMzY3NDY90", # Central Zone
    # "https://results.advancedeventsystems.com/event/PTAwMDAwMzY5MTI90", # Nike Classic
    "https://results.advancedeventsystems.com/event/PTAwMDAwMzgzNjE90" # 2025 NIT
    # Add more event IDs here
]

# Streamlit App Title
st.title("🏐 Volleyball Match Results")

# Initialize session state for caching API data
if "aes_all_data" not in st.session_state:
    st.session_state["aes_all_data"] = pd.DataFrame()
if "aes_match_results" not in st.session_state:
    st.session_state["aes_match_results"] = pd.DataFrame()
if "data_fetched" not in st.session_state:
    st.session_state["data_fetched"] = False  # Flag to indicate if data is fetched

# Function to fetch and process event data
def process_event(url):
    match = re.search(r'/event/([^/]+)$', url)
    event_id = match.group(1) if match else None

    print(f"Processing event ID: {event_id}")
    
    # Define the base API endpoint for the event
    base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}"
    response = requests.get(base_url)
    if response.status_code != 200:
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")
        return pd.DataFrame()

    event_data = response.json()
    event_name = event_data.get("Name", f"Event_{event_id}")
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
                    "TeamName": team["TeamName"],
                    "TeamCode": team["TeamCode"],
                    "OriginalTeamCode": team["TeamCode"],
                    "AESTeamID": team["TeamId"],
                    "FinishRank": f"{team['FinishRank']} ({team['Division']['Name']})",
                    "DivisionName": team["Division"]["Name"],
                    "DivisionID": team["Division"]["DivisionId"],
                    "EventName": event_name,
                }
                for team in standings_data.get("value", [])
            ])
        else:
            print(f"Failed to fetch standings for division ID: {division_id}. Status code: {response.status_code}")
    
    results = process_match_results(teams, event_id, event_name)
    print(f"Finished processing {event_name}")
    
    return pd.DataFrame(teams), results


from datetime import datetime

def process_match_results(team_list, event_id, event_name):
    match_list = []
    
    for team in team_list:
        aes_teamID = team["AESTeamID"]
        division_id = team["DivisionID"]
        base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}/division/{division_id}/team/{aes_teamID}/schedule/past"
        
        response = requests.get(base_url)
        if response.status_code != 200:
            print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")
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
            
            # Extract match date & time
            scheduled_datetime = match.get("ScheduledStartDateTime", "")
            match_day, match_time = "N/A", "N/A"

            if scheduled_datetime:
                dt = datetime.fromisoformat(scheduled_datetime)  # Convert to datetime object
                match_day = dt.strftime("%A, %B %d, %Y")  # Example: "Saturday, January 18, 2025"
                match_time = dt.strftime("%I:%M %p").lstrip("0")  # Example: "8:30 AM"

            # Extract set scores and ensure a max of 3 sets
            set_scores = [set_data["ScoreText"] for set_data in match["Sets"] if set_data["ScoreText"]]
            while len(set_scores) < 3:  # Fill missing sets with empty values
                set_scores.append("")

            # Calculate margin of victory for each set
            margins = []
            for set_score in set_scores:
                if "-" in set_score:  # Ensure valid score format
                    scores = list(map(int, set_score.split("-")))
                    margins.append(abs(scores[0] - scores[1]))
                else:
                    margins.append(None)  # Empty or invalid score
            
            # Determine match result
            winner = first_team_name if first_team_won else second_team_name
                
            match_list.append({
                "Event Name": event_name,
                "Match ID": match_id,
                "Match Day": match_day,  # ✅ Added match day
                "Match Time": match_time,  # ✅ Added match time
                "First Team ID": first_team_id,
                "First Team Name": first_team_name,
                "Second Team ID": second_team_id,
                "Second Team Name": second_team_name,
                "Winner": winner,
                "Set 1": set_scores[0],
                "Set 2": set_scores[1],
                "Set 3": set_scores[2],
                "Margin Set 1": margins[0],
                "Margin Set 2": margins[1],
                "Margin Set 3": margins[2]
            })
            
    # Convert list to DataFrame
    df = pd.DataFrame(match_list)
    
    # Remove duplicates based on Match ID
    df = df.drop_duplicates(subset=["Match ID"], keep="first")

    return df



# Function to process match results
# def process_match_results(team_list, event_id, event_name):
#     match_list = []
    
#     for team in team_list:
#         aes_teamID = team["AESTeamID"]
#         division_id = team["DivisionID"]
#         base_url = f"https://results.advancedeventsystems.com/api/event/{event_id}/division/{division_id}/team/{aes_teamID}/schedule/past"
        
#         response = requests.get(base_url)
#         if response.status_code != 200:
#             print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")
#             return pd.DataFrame()
        
#         data = response.json()
        
#         # Iterate through matches and extract details
#         for match_data in data:
#             match = match_data["Match"]
            
#             match_id = match["MatchId"]
#             first_team_id = match["FirstTeamId"]
#             first_team_name = match["FirstTeamName"]
#             first_team_won = match["FirstTeamWon"]
#             second_team_id = match["SecondTeamId"]
#             second_team_name = match["SecondTeamName"]
            
#             # Extract set scores
#             set_scores = [set_data["ScoreText"] for set_data in match["Sets"] if set_data["ScoreText"]]

#             # Determine match result
#             winner = first_team_name if first_team_won else second_team_name
                
#             match_list.append({
#                 "Event Name": event_name,
#                 "Match ID": match_id,
#                 "First Team ID": first_team_id,
#                 "First Team Name": first_team_name,
#                 "Second Team ID": second_team_id,
#                 "Second Team Name": second_team_name,
#                 "Winner": winner,
#                 "Set Scores": ", ".join(set_scores)
#             })
            
#     # Convert list to DataFrame
#     df = pd.DataFrame(match_list)
    
#     # Remove duplicates based on Match ID
#     df = df.drop_duplicates(subset=["Match ID"], keep="first")

#     return df


# Button to fetch match data (Only runs once and caches the data)
if st.button("Fetch Match Data") or not st.session_state["data_fetched"]:
    combined_data = pd.DataFrame()
    match_results = pd.DataFrame()

    for url in aes_urls:
        event_data, results = process_event(url)
        combined_data = pd.concat([combined_data, event_data], ignore_index=True)
        match_results = pd.concat([match_results, results], ignore_index=True)
    
    # Store fetched data in session state
    st.session_state["aes_all_data"] = combined_data
    st.session_state["aes_match_results"] = match_results
    st.session_state["data_fetched"] = True  # Mark data as fetched


# Fetch stored data from session state
aes_all_data = st.session_state["aes_all_data"]
aes_match_results = st.session_state["aes_match_results"]

# Get unique team names for dropdown
all_teams = sorted(set(aes_match_results["First Team Name"]).union(set(aes_match_results["Second Team Name"])))

# Dropdown to select a team
selected_team = st.selectbox("Select a Team to Filter Matches", ["All Teams"] + all_teams)

# Filter the DataFrame based on the selected team
filtered_results = aes_match_results.copy()
if selected_team != "All Teams":
    filtered_results = filtered_results[(filtered_results["First Team Name"] == selected_team) | (filtered_results["Second Team Name"] == selected_team)]

# Function to highlight winner cell
def highlight_winner(s):
    if selected_team != "All Teams":
        return [f"background-color: {'lightgreen' if v == selected_team else 'lightcoral'}; color: black" for v in s]
    return [""] * len(s)

# Apply styling only to the Winner column
styled_df = filtered_results.style.apply(highlight_winner, subset=["Winner"])

# Display DataFrame in Streamlit
st.subheader("📋 Match Results")
st.dataframe(styled_df)

# Allow CSV download
csv = filtered_results.to_csv(index=False).encode("utf-8")
st.download_button(label="📥 Download CSV", data=csv, file_name="filtered_match_results.csv", mime="text/csv")
