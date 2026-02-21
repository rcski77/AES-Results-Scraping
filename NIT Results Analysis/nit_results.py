import re
import requests
import pandas as pd


# First list of event IDs to process normally - current year's events
aes_urls = [
    "https://results.advancedeventsystems.com/event/PTAwMDAwNDI3Nzk90",  # 2026 NIT
    # Add more event IDs here
]

# Initialize an empty DataFrame to hold all data
aes_all_data = pd.DataFrame()
aes_match_results = pd.DataFrame()

print("Volleyball Match Results")


def parse_set_scores(set_scores_text):
    parsed_sets = []
    if not isinstance(set_scores_text, str) or not set_scores_text.strip():
        return parsed_sets

    for score_text in set_scores_text.split(","):
        score_text = score_text.strip()
        match = re.match(r"^(\d+)\s*-\s*(\d+)$", score_text)
        if match:
            team_one_score = int(match.group(1))
            team_two_score = int(match.group(2))
            parsed_sets.append((team_one_score, team_two_score))

    return parsed_sets


def calculate_weekend_metrics(match_results_df):
    total_matches = len(match_results_df)
    matches_went_three_sets = 0
    total_set_margin = 0
    total_sets = 0
    two_point_sets = 0
    extra_point_sets = 0

    for _, row in match_results_df.iterrows():
        parsed_sets = parse_set_scores(row.get("Set Scores", ""))

        if len(parsed_sets) >= 3:
            matches_went_three_sets += 1

        for set_index, (team_one_score, team_two_score) in enumerate(parsed_sets):
            margin = abs(team_one_score - team_two_score)
            total_set_margin += margin
            total_sets += 1
            if margin == 2:
                two_point_sets += 1
            
            # Check if set went to extra points
            # For sets 1-2: a team scored 25+ points
            # For set 3: a team scored 15+ points
            is_set_three = set_index == 2
            threshold = 15 if is_set_three else 25
            if team_one_score > threshold or team_two_score > threshold:
                extra_point_sets += 1

    third_set_pct = (matches_went_three_sets / total_matches * 100) if total_matches else 0
    avg_margin = (total_set_margin / total_sets) if total_sets else 0
    two_point_set_pct = (two_point_sets / total_sets * 100) if total_sets else 0
    extra_point_set_pct = (extra_point_sets / total_sets * 100) if total_sets else 0

    return {
        "total_matches": total_matches,
        "matches_went_three_sets": matches_went_three_sets,
        "third_set_pct": third_set_pct,
        "average_set_margin": avg_margin,
        "two_point_sets": two_point_sets,
        "total_sets": total_sets,
        "two_point_set_pct": two_point_set_pct,
        "extra_point_sets": extra_point_sets,
        "extra_point_set_pct": extra_point_set_pct,
    }

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
        print(f"Failed to fetch event details for event ID: {event_id}. Status code: {response.status_code}")
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

if aes_match_results.empty:
    print("No match results found.")
else:
    print("\nMatch Results (one line per match)")
    for _, row in aes_match_results.iterrows():
        print(
            f"Match ID {row['Match ID']}: "
            f"{row['First Team Name']} vs {row['Second Team Name']} | "
            f"Winner: {row['Winner']} | "
            f"Set Scores: {row['Set Scores']}"
        )

    metrics = calculate_weekend_metrics(aes_match_results)
    print("\nWeekend Summary")
    print(
        f"Matches that went to a 3rd set: {metrics['matches_went_three_sets']} "
        f"/ {metrics['total_matches']} ({metrics['third_set_pct']:.1f}%)"
    )
    print(
        f"Average margin of victory (per set): {metrics['average_set_margin']:.2f} points"
    )
    print(
        f"Sets decided by 2 points: {metrics['two_point_sets']} / {metrics['total_sets']} "
        f"({metrics['two_point_set_pct']:.1f}%)"
    )
    print(
        f"Sets that went to extra points: {metrics['extra_point_sets']} / {metrics['total_sets']} "
        f"({metrics['extra_point_set_pct']:.1f}%)"
    )