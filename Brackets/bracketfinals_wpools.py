import requests
import pandas as pd
import json

AesId = "PTAwMDAwNDAzMTM90"
Date = "2025-07-03"

# First, get the event info to extract division IDs and names
event_url = f"https://results.advancedeventsystems.com/api/event/{AesId}"
event_response = requests.get(event_url)
if event_response.status_code != 200:
    print(f"Failed to fetch event data: {event_response.status_code}")
    exit(1)

event_data = event_response.json()
divisions = event_data.get("Divisions", [])

division_list = []
for division in divisions:
    division_id = division.get("DivisionId")
    division_name = division.get("Name")
    division_list.append({"DivisionId": division_id, "Name": division_name})

print("Divisions in event:")
for d in division_list:
    print(f"  {d['DivisionId']}: {d['Name']}")

finals_rows = []

for div in division_list:
    division_id = div["DivisionId"]
    division_name = div["Name"]
    url = f"https://results.advancedeventsystems.com/api/event/{AesId}/division/{division_id}/plays/{Date}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data for division {division_id}: {response.status_code}")
        continue
    data = response.json()
    for bracket in data:
        # If this is a pool (no Roots, but has Teams), call the poolsheet API and record all matches
        if "Teams" in bracket and "Roots" not in bracket:
            pool_playid = bracket.get("PlayId")
            pool_name = bracket.get("FullName", "Unknown Pool")
            pool_short_name = bracket.get("ShortName", "")
            pool_url = f"https://results.advancedeventsystems.com/api/event/{AesId}/poolsheet/{pool_playid}"
            pool_response = requests.get(pool_url)
            if pool_response.status_code == 200:
                pool_data = pool_response.json()
                matches = pool_data.get("Matches", [])
                for match in matches:
                    match_name = match.get("MatchFullName", "Unknown Match")
                    scheduled_time = match.get("ScheduledStartDateTime", "Unknown Time")
                    court = match.get("Court", {}).get("Name", "Unknown Court")
                    finals_rows.append({
                        "Division": division_name,
                        "Bracket": f"{pool_name} (Pool)",
                        "Match": match_name,
                        "Time": scheduled_time,
                        "Court": court
                    })
            continue
        bracket_name = bracket.get("FullName", "Unknown Bracket")
        bracket_short_name = bracket.get("ShortName", "")
        roots = bracket.get("Roots", [])
        if not roots or "Match" not in roots[0]:
            continue
        finals_match = roots[0]["Match"]
        match_name = finals_match.get("FullName", "Unknown Match")
        scheduled_time = finals_match.get("ScheduledStartDateTime", "Unknown Time")
        court = finals_match.get("Court", {}).get("Name", "Unknown Court")
        finals_rows.append({
            "Division": division_name,
            "Bracket": bracket_name,
            "Match": match_name,
            "Time": scheduled_time,
            "Court": court
        })

        # If bracket is Gold, also record the first matches under TopSource and BottomSource (semifinals)
        if bracket_short_name.lower() == "gold":
            root = roots[0]
            for source_type in ["TopSource", "BottomSource"]:
                source = root.get(source_type)
                if source and "Match" in source:
                    semi_match = source["Match"]
                    semi_match_name = semi_match.get("FullName", "Unknown Match")
                    semi_scheduled_time = semi_match.get("ScheduledStartDateTime", "Unknown Time")
                    semi_court = semi_match.get("Court", {}).get("Name", "Unknown Court")
                    finals_rows.append({
                        "Division": division_name,
                        "Bracket": f"{bracket_name} (Semifinal)",
                        "Match": semi_match_name,
                        "Time": semi_scheduled_time,
                        "Court": semi_court
                    })

# Create DataFrame
finals_df = pd.DataFrame(finals_rows)

# Split the 'Time' column into 'Date' and 'Time', format time as am/pm
if not finals_df.empty:
    finals_df['Date'] = pd.to_datetime(finals_df['Time'], errors='coerce').dt.date.astype(str)
    finals_df['Time'] = pd.to_datetime(finals_df['Time'], errors='coerce').dt.strftime('%I:%M %p')

print("\nAll Finals:")
print(finals_df)

# Export DataFrame to CSV
finals_df.to_csv("all_bracket_finals.csv", index=False)
print("\nFinals exported to all_bracket_finals.csv")