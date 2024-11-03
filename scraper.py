import asyncio
import calendar
import json
import os
import time
from collections import defaultdict

import httpx
import tqdm

from parsers import parse_base_data, parse_base_url, parse_match_html
from utils import HEADERS, fetch_url, write_file
from logger import logger

def fetch_base_data(retry: int = 0) -> None:
    """Save all regions and top matches to a JSON file.

    Regions doesn't change often, so we can save it once and use it later.
    """

    def _retry():
        if retry < 3:
            time.sleep(1)
            return fetch_base_data(retry=retry + 1)
        logger.error("Failed to fetch base data after 3 retries. url: https://www.whoscored.com/")
        raise Exception("Failed to fetch base data")

    client = httpx.Client(headers=HEADERS)

    response = client.get("https://www.whoscored.com/")
    if response.status_code != 200:
        return _retry()

    parse_base_data(response.content.decode("utf-8"))


async def get_tournaments_by_month(
    client: httpx.AsyncClient,
    base_url: str,
) -> dict[str, list[dict]]:
    tasks = [fetch_url(client, base_url.format(month=month)) for month in range(1, 13)]
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
    tournaments_by_month: dict[str, list[dict]],
    base_url: str,
    league_name: str,
) -> list[str]:
    match_urls = []
    for month, tournaments in tournaments_by_month.items():
        os.makedirs(f"matches/{league_name}/{month}", exist_ok=True)
        write_file(
            f"matches/{league_name}/{month}/matches.json",
            tournaments,
            is_json=True,
        )

        matches = []
        for tournament in tournaments:
            matches.extend(tournament.get("matches", []))

        if not matches:
            continue

        for match in matches:
            home_team = match["homeTeamName"].replace(" ", "-").replace(".", "")
            away_team = match["awayTeamName"].replace(" ", "-").replace(".", "")
            match_url = base_url.format(
                match_id=match["id"],
                home_team=home_team,
                away_team=away_team,
                month=month,
            )
            match_urls.append(match_url)

    return match_urls


async def get_matches_by_month(base_url: str) -> None:
    base_match_url, base_data_url, league_name = parse_base_url(base_url)

    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    async with httpx.AsyncClient(headers=HEADERS, limits=limits) as client:
        tournaments = await get_tournaments_by_month(client, base_data_url)
        match_urls = find_matches_url_by_tournaments(
            tournaments,
            base_match_url,
            league_name,
        )
        tasks = [fetch_url(client, url) for url in match_urls]
        responses = await asyncio.gather(*tasks)

    html_contents = []
    for response, url in tqdm.tqdm(zip(responses, match_urls), total=len(match_urls)):
        month = url.split("x-month=")[1]
        match_id = url.split("/")[4]

        content = response.decode("utf-8")
        html_contents.append(content)
        write_file(f"matches/{league_name}/{month}/raw_html_{match_id}.html", content)

        parse_match_html(content, month, league_name)
