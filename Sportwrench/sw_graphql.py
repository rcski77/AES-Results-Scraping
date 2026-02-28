import asyncio
import json

from playwright.async_api import async_playwright

EVENT_ESW_ID = "bc1b1a9e9"


async def fetch_graphql():
    url = "https://events2.sportwrench.com/api/esw/graphql"

    event_query = """
    query EventDetails($eswId: ID!) {
      event(id: $eswId) {
        id
        long_name
        city
        state
        tickets_published
        schedule_published
        is_require_recipient_name_for_each_ticket
        tickets_code
        allow_point_of_sales
        sales_hub_point_of_sale_id
        hide_seeds
        days
        has_rosters
        is_with_prev_qual
        event_notes
        address
        third_party_settings
        sport_sanctioning
        locations {
          location_name
        }
        teams_settings {
          baller_tv_available
          aim_streaming_available
          hide_standings
          sort_by
          manual_club_names
        }
      }
      divisions(eventKey: $eswId) {
        division_id
        name
        teams_count
        short_name
        has_flow_chart
        media(filterFileTypes: ["flowchart"]) {
          media_id
          division_id
          file_type
          path
        }
        matches_time_ranges {
          day
          start_time
          end_time
        }
        rounds {
          uuid
          division_id
          sort_priority
          name
          short_name
          first_match_start
          last_match_start
        }
      }
    }
    """

    division_standings_query = """
    query DivisionTeamsStanding($eswId: ID!, $divisionId: ID!) {
      divisionTeamsStanding(eventKey: $eswId, divisionId: $divisionId) {
        team_id
        team_name
        team_code
        extra {
          show_previously_accepted_bid
          show_accepted_bid
          __typename
        }
        division_standing {
          matches_won
          matches_lost
          sets_won
          sets_lost
          sets_pct
          points_ratio
          points
          rank
          seed
          heading
          __typename
        }
        __typename
      }
    }
    """

    event_variables = {"eswId": EVENT_ESW_ID}
    event_id = event_variables["eswId"]
    headless = False

    async def run_once(headless: bool, gql_query: str, gql_variables: dict) -> dict:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            try:
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(
                    f"https://events2.sportwrench.com/events/{event_id}/divisions",
                    wait_until="domcontentloaded",
                )
                await page.wait_for_timeout(1500)

                fetch_result = await page.evaluate(
                    """async ({ url, query, variables }) => {
                        const res = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({ query, variables })
                        });

                        const contentType = res.headers.get('content-type') || '';
                        const text = await res.text();

                        return {
                            ok: res.ok,
                            status: res.status,
                            contentType,
                            text
                        };
                    }""",
                    {"url": url, "query": gql_query, "variables": gql_variables},
                )
            finally:
                await browser.close()

        content_type = fetch_result["contentType"].lower()
        body_text = fetch_result["text"]

        if "application/json" in content_type:
            try:
                return json.loads(body_text)
            except json.JSONDecodeError:
                pass

        snippet = body_text[:500].replace("\n", " ").strip()
        raise RuntimeError(
            "GraphQL endpoint returned non-JSON response "
            f"(status={fetch_result['status']}, content-type='{fetch_result['contentType']}'). "
            f"Body starts with: {snippet}"
        )

    response_json = await run_once(
        headless=headless,
        gql_query=event_query,
        gql_variables=event_variables,
    )

    divisions = response_json.get("data", {}).get("divisions", [])
    division_ids = [division.get("division_id") for division in divisions if division.get("division_id")]
    print("Division IDs:", division_ids)

    division_standings = []
    for division_id in division_ids:
        standing_variables = {
            "eswId": EVENT_ESW_ID,
            "divisionId": division_id,
        }

        standings_response = await run_once(
            headless=headless,
            gql_query=division_standings_query,
            gql_variables=standing_variables,
        )

        teams = standings_response.get("data", {}).get("divisionTeamsStanding", [])
        division_standings.append(
            {
                "division_id": division_id,
                "teams": teams,
            }
        )

    print(f"Fetched standings for {len(division_standings)} divisions")
    print(json.dumps(division_standings, indent=2))


asyncio.run(fetch_graphql())
