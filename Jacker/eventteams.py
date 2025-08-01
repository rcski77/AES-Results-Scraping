import requests
import pandas as pd

def pull_jacker_teams(jacker_id):
    """
    Fetches team data from the API based on the given jacker_id,
    adds a '2025NIT' column, creates a pivot table with 'TeamCode' as the index.

    Args:
        jacker_id (int): The ID to fetch data from the API.

    Returns:
        pd.DataFrame: The pivot table as a pandas DataFrame.
    """
    # API endpoint
    url = f"https://www.triplecrownsports.com/Data/UAGetTeams/?id={jacker_id}"
    
    # Fetch data from the API
    response = requests.get(url)
    
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()
        
        # Convert JSON data to a pandas DataFrame
        df = pd.DataFrame(data)
        
        # Convert TeamCode to lowercase
        df["TeamCode"] = df["TeamCode"].str.lower()

        # Create a pivot table with TeamCode as the index and include all columns
        pivot_table = df.set_index("TeamCode").reset_index()
        
        print(f"Pulled data from Jacker")
        # Save the pivot table to a CSV file
        pivot_table.to_csv(f"jacker_teams_{jacker_id}.csv", index=False)
        return pivot_table
    else:
        print(f"Failed to fetch data from the API. Status code: {response.status_code}")
        return None
    
if __name__ == "__main__":
    pull_jacker_teams(10729)