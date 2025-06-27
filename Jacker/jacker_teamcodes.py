import requests
import pandas as pd

# API endpoint with the jackerID
jacker_id = 10570 # West Coast Invite
url = f"https://www.triplecrownsports.com/Data/UAGetTeams/?id={jacker_id}"

# Fetch data from the API
response = requests.get(url)

# Check if the API call was successful
if response.status_code == 200:
    # Parse JSON response
    data = response.json()
    
    # Convert JSON data to a pandas DataFrame
    df = pd.DataFrame(data)
    
     # Convert TeamCode to lowercase
    df["TeamCode"] = df["TeamCode"].str.lower()
    
    # Create a pivot table with TeamCode as the index
    pivot_table = df.pivot_table(
        index="TeamName",
        values=[col for col in df.columns if col != "TeamName"],
        aggfunc="first"
    ).reset_index()
    
    # Import the CSV file into a pandas DataFrame
    import os
    csv_filename = "ConfirmedRegistrations-10570.csv"
    if not os.path.isfile(csv_filename):
        raise FileNotFoundError(f"CSV file '{csv_filename}' not found in the current directory.")
    confirmed_registrations_df = pd.read_csv(csv_filename)
    
    # Merge the pivot_table and confirmed_registrations_df on 'TeamName'
    merged_df = pd.merge(pivot_table, confirmed_registrations_df, on="TeamName", how="inner")
    # Remove 'TeamCode' and 'Product' columns if they exist
    merged_df = merged_df.drop(columns=[col for col in ['Team Code', 'Product'] if col in merged_df.columns])
    
    # Save the pivot table to a CSV file
    csv_file_path = "team_pivot_table.csv"
    merged_df.to_csv(csv_file_path, index=False)
    
    print(f"Pivot table saved to {csv_file_path}")
else:
    print(f"Failed to fetch data from the API. Status code: {response.status_code}")
