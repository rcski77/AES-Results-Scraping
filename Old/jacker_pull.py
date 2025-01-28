import requests
import pandas as pd

# API endpoint with the jackerID
jacker_id = 10526
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
    
    # Add the 2025NIT column with "Yes" for all rows
    df["2025NIT"] = "Yes"
    
    # Create a pivot table with TeamCode as the index
    pivot_table = df.pivot_table(
        index="TeamCode", 
        values="2025NIT", 
        aggfunc="first"  # Ensures the column remains "Yes"
    ).reset_index()
    
    # Save the pivot table to a CSV file
    csv_file_path = "team_pivot_table.csv"
    pivot_table.to_csv(csv_file_path, index=False)
    
    print(f"Pivot table saved to {csv_file_path}")
else:
    print(f"Failed to fetch data from the API. Status code: {response.status_code}")
