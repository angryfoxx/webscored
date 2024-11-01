import asyncio
import glob
import json
import os

import httpx

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


def find_match_files():
    pattern = os.path.join("matches", "**", "match_centre_data_*.json")

    match_files = glob.glob(pattern, recursive=True)

    return match_files
