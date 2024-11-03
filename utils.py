import asyncio
import glob
import json
import os

import httpx
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

from logger import logger

HEADERS = {
    "Dnt": "1",
    "Priority": "u=0, i",
    "Referer": "https://www.google.com/",
    "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Microsoft Edge";v="126"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0,Test",  # noqa: E501
}


async def fetch_url(client, url: str, retry: int = 0) -> bytes:
    async def _retry():
        if retry < 3:
            await asyncio.sleep(1)
            return await fetch_url(client, url, retry=retry + 1)
        logger.error("Failed to fetch %s after 3 retries", url)
        return b""

    try:
        response = await client.get(url)
        if response.status_code == 200:
            return response.content
        return await _retry()
    except httpx.HTTPError:
        return await _retry()


def write_file(file_name, content, is_json=False):
    with open(file_name, "w", encoding="utf-8") as file:
        if is_json:
            json.dump(content, file, ensure_ascii=False, indent=4)
        else:
            file.write(content)


async def find_valid_urls(tournament_urls: list[str]) -> None:
    """We have a list of URLs that has not season id and stage id.

    We need to find full URLs that contain season id and stage id.
    """
    logger.info("Finding valid URLs...")
    tournament_url_mapping = {}

    if os.path.exists("matches/tournament_url_mapping.json"):
        with open("matches/tournament_url_mapping.json", "r", encoding="utf-8") as f:
            existing_tournament_url_mapping = json.load(f)
            existing_tournament_url_mapping.update(tournament_url_mapping)
            tournament_url_mapping = existing_tournament_url_mapping

    tournament_urls = tuple(
        filter(lambda url: url not in tournament_url_mapping, tournament_urls)
    )
    if not tournament_urls:
        return

    async with httpx.AsyncClient(headers=HEADERS) as client:
        responses = []
        for url in tqdm(tournament_urls, desc="Finding valid URLs"):
            response = await fetch_url(client, url)
            responses.append(response)

        for response, url in tqdm(
            zip(responses, tournament_urls),
            desc="Finding valid URLs",
        ):
            if not response:
                continue

            soup = BeautifulSoup(response, "lxml")
            canonical_link = soup.find("link", {"rel": "canonical"})
            if not canonical_link:
                logger.error("No valid link found for %s", url)
                continue

            valid_url = canonical_link["href"]
            tournament_url_mapping[url] = valid_url

        write_file(
            "matches/tournament_url_mapping.json", tournament_url_mapping, is_json=True
        )


def find_incident_event_files():
    pattern = os.path.join("matches", "**", "match_centre_data_*.json")

    match_files = glob.glob(pattern, recursive=True)

    return match_files


def find_match_files():
    pattern = os.path.join("matches", "**", "matches*.json")

    match_files = glob.glob(pattern, recursive=True)

    return match_files
