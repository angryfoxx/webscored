import asyncio
import glob
import json
import os

import httpx
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm

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
        print(f"Failed to fetch {url}")
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
    print("\033[93mFinding valid URLs...\033[0m")
    tournament_url_mapping = {}

    if os.path.exists("matches/tournament_url_mapping.json"):
        with open("matches/tournament_url_mapping.json", "r", encoding="utf-8") as f:
            existing_tournament_url_mapping = json.load(f)
            existing_tournament_url_mapping.update(tournament_url_mapping)
            tournament_url_mapping = existing_tournament_url_mapping

    tournament_urls = tuple(
        filter(lambda url: url not in tournament_url_mapping, tournament_urls)
    )

    async with httpx.AsyncClient(headers=HEADERS) as client:
        tasks = [fetch_url(client, url) for url in tournament_urls]
        responses = await asyncio.gather(*tasks)

        for response, url in tqdm(
            zip(responses, tournament_urls),
            desc="Finding valid URLs",
        ):
            if not response:
                continue

            soup = BeautifulSoup(response, "lxml")
            canonical_link = soup.find("link", {"rel": "canonical"})
            if not canonical_link:
                print(f"\033[91mNo valid link found for {url}\033[0m")
                continue

            valid_url = canonical_link["href"]
            tournament_url_mapping[url] = valid_url

        write_file(
            "matches/tournament_url_mapping.json", tournament_url_mapping, is_json=True
        )


def find_match_files():
    pattern = os.path.join("matches", "**", "match_centre_data_*.json")

    match_files = glob.glob(pattern, recursive=True)

    return match_files
