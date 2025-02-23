from scrapling import StealthyFetcher
import pandas as pd

fetcher = StealthyFetcher(auto_match=False)
sportwrench_data = pd.DataFrame()

# Sportwrench Event URLs
sw_event_urls = [
    # "https://events.sportwrench.com/#/events/6583cabd2",
    # "https://events.sportwrench.com/#/events/abbfb1d13",
    # "https://events.sportwrench.com/#/events/870cf0151",
    # "https://events.sportwrench.com/#/events/7ccb7d73a",
    # "https://events.sportwrench.com/#/events/aac1370ff",
    # "https://events.sportwrench.com/#/events/e73a9d3b3",
    "https://events.sportwrench.com/#/events/c098ff439"
]


def process_event(url):
    event_id = url.rsplit("/", 1)[-1]
    
    # Define the base API endpoint for the event 
    base_url = f"https://events.sportwrench.com/api/esw/{event_id}"
    
    page = fetcher.fetch(base_url)
    if (page.status != 200):
        print(f"Failed to fetch event details for event ID: {
              event_id}. Status code: {page.status}")
        return pd.DataFrame()
    
    content = page.json()
    event_name = content.get('long_name')
    print(f"Processing {event_name} / ID: {event_id}")
    
    #Get all divisions and IDs for event
    division_url = f"https://events.sportwrench.com/api/esw/{event_id}/divisions"
    div_page = fetcher.fetch(division_url)
    if (div_page.status == 200):
        division_content = div_page.json()
        division_ids = [division["division_id"] for division in division_content]
        
        for division_id in division_ids:
            standings_url =f"https://events.sportwrench.com/api/esw/{event_id}/divisions/{division_id}/standings"
            standings_page = fetcher.fetch(standings_url)
            if (standings_page.status == 200):
                standings_content = standings_page.json()
                
                # Extract data into a list
                teams_list = []
                for division, teams in standings_content["teams"].items():
                    for team in teams:
                        teams_list.append({
                            "Division": division,
                            "Seed": team["seed_current"],
                            "Team Name": team["team_name"],
                            "Organization Code": team["organization_code"],
                         })
                df = pd.DataFrame(teams_list)
    
    return df


# Process URLs in Sportwrench list    
for url in sw_event_urls:
    sportwrench_data = pd.concat([sportwrench_data, process_event(url)], ignore_index=True)
    
print(sportwrench_data)