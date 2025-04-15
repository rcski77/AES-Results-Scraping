import asyncio
from playwright.async_api import async_playwright
import json

async def fetch_graphql():
    url = "https://events2.sportwrench.com/api/esw/graphql"

    query = """
    query PaginatedDivisionTeams($eswId: ID!, $divisionId: ID!, $page: Float!, $pageSize: Float!, $search: String) {
      paginatedDivisionTeams(
        eventKey: $eswId,
        divisionId: $divisionId,
        page: $page,
        pageSize: $pageSize,
        search: $search
      ) {
        items {
          team_id
          team_name
          division_id
          next_match {
            secs_start
            external {
              opponent_display_name
              court_info { short_name }
            }
          }
          division_standing {
            matches_won
            matches_lost
            sets_won
            sets_lost
            rank
          }
        }
        page_info {
          page
          page_size
          page_count
          item_count
        }
      }
    }
    """

    variables = {
        "eswId": "090be3e48",
        "divisionId": "18747",
        "page": 1,
        "pageSize": 20,
        "search": ""
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to the home page to pass Cloudflare
        await page.goto("https://events2.sportwrench.com/events/090be3e48/divisions", wait_until="domcontentloaded")

        # Now make the fetch call inside the browser page context
        response_json = await page.evaluate(
            """async ({ url, query, variables }) => {
                const res = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ query, variables })
                });
                return await res.json();
            }""",
            {"url": url, "query": query, "variables": variables}
        )

        print(json.dumps(response_json, indent=2))
        await browser.close()

asyncio.run(fetch_graphql())
