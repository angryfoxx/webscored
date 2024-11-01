import asyncio
import calendar
import json
import os
from collections import defaultdict

import httpx
import tqdm

from parsers import parse_match_html
from utils import HEADERS, fetch_url, write_file


async def get_tournaments_by_month(client) -> dict[str, list[dict]]:
    url_template = "https://www.whoscored.com/tournaments/23430/data/?d=2024{month:02d}&isAggregate=false"
    tasks = [
        fetch_url(client, url_template.format(month=month)) for month in range(1, 13)
    ]
    responses = await asyncio.gather(*tasks)

    tournaments_by_month = defaultdict(list)
    for response, month in zip(responses, range(1, 13)):
        try:
            tournament_data = json.loads(response)
            tournaments = tournament_data.get("tournaments", [])
            if not tournaments:
                continue

            tournaments_by_month[calendar.month_name[month]].extend(tournaments)
        except json.JSONDecodeError:
            continue

    return tournaments_by_month


def find_matches_url_by_tournaments(
    tournaments_by_month: dict[str, list[dict]]
) -> list[str]:
    match_urls = []
    for month, tournaments in tournaments_by_month.items():
        os.makedirs(f"matches/{month}", exist_ok=True)
        write_file(f"matches/{month}/matches.json", tournaments, is_json=True)

        matches = []
        for tournament in tournaments:
            matches.extend(tournament.get("matches", []))

        if not matches:
            continue

        for match in matches:
            home_team = match["homeTeamName"].replace(" ", "-").replace(".", "")
            away_team = match["awayTeamName"].replace(" ", "-").replace(".", "")
            # x-month is used to indicate the month of the match in the URL for development purposes.
            match_url = f"https://www.whoscored.com/Matches/{match['id']}/Live/England-League-Cup-2024-2025-{home_team}-{away_team}?x-month={month}"
            match_urls.append(match_url)

    return match_urls


async def get_matches_by_month() -> list[str]:
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits) as client:
        tournaments = await get_tournaments_by_month(client)
        match_urls = find_matches_url_by_tournaments(tournaments)
        tasks = [fetch_url(client, url) for url in match_urls]
        responses = await asyncio.gather(*tasks)

    html_contents = []
    for response, url in tqdm.tqdm(zip(responses, match_urls), total=len(match_urls)):
        month = url.split("x-month=")[1]
        match_id = url.split("/")[4]

        content = response.decode("utf-8")
        html_contents.append(content)
        write_file(f"matches/{month}/raw_html_{match_id}.html", content)

        parse_match_html(content, month)

    return html_contents
