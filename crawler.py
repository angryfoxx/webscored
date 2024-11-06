import asyncio
import calendar
import json
import os
import time
from collections import defaultdict

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from tqdm.asyncio import tqdm

from constants import CONCURRENCY_LIMIT, RETRY_LIMIT
from logger import logger
from parsers import parse_base_url, parse_match_html
from scraper import find_matches_url_by_tournaments
from utils import HEADERS, write_file


def fetch_page_content_sync(
    page,
    url: str,
    save_path: str | None = None,
    save_file=True,
):
    """
    Fetches the page content using a Playwright page instance and saves it to a specified path.

    Args:
        page (Page): The Playwright page instance.
        url (str): The URL to scrape.
        save_path (str): The file path to save the scraped content.
        save_file (bool): Whether to save the content to a file or not.
    """
    for attempt in range(RETRY_LIMIT):
        try:
            page.goto(url, wait_until="domcontentloaded")
            content = page.content()
            if "525: SSL handshake failed" in content:
                raise Exception("SSL handshake failed")

            if not save_file:
                return content
            write_file(save_path, content)
            logger.info(f"Successfully fetched content from {url}")
            return  # Exit on successful fetch
        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1} to fetch content from {url} failed: {e}"
            )
            if attempt + 1 == RETRY_LIMIT:
                logger.error(
                    f"Failed to fetch content from {url} after {RETRY_LIMIT} attempts"
                )

            time.sleep(1)


async def fetch_page_content(
    page,
    url: str,
    save_path: str | None = None,
    save_file=True,
):
    """
    Fetches the page content using a Playwright page instance and saves it to a specified path.

    Args:
        page (Page): The Playwright page instance.
        url (str): The URL to scrape.
        save_path (str): The file path to save the scraped content.
        save_file (bool): Whether to save the content to a file or not.
    """
    for attempt in range(RETRY_LIMIT):
        try:
            await page.goto(url, wait_until="domcontentloaded")
            content = await page.content()
            if "525: SSL handshake failed" in content:
                raise Exception("SSL handshake failed")

            if not save_file:
                return content
            write_file(save_path, content)
            logger.info(f"Successfully fetched content from {url}")
            return  # Exit on successful fetch
        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1} to fetch content from {url} failed: {e}"
            )
            if attempt + 1 == RETRY_LIMIT:
                logger.error(
                    f"Failed to fetch content from {url} after {RETRY_LIMIT} attempts"
                )
            await asyncio.sleep(1)

async def get_tournaments_by_month_by_pw(base_data_url: str) -> dict[str, list[dict]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)  # Limit concurrent tasks

        responses = []
        async with semaphore:
            for month in range(1, 13):
                page = await browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                content = await fetch_page_content(
                    page, base_data_url.format(month=month), None, save_file=False
                )
                responses.append(content)
                await page.close()

        await browser.close()

    tournaments_by_month = defaultdict(list)
    for response, month in zip(responses, range(1, 13)):
        try:
            response = response.replace("</body></html>", "").replace(
                "<html><head></head><body>", ""
            )
            tournament_data = json.loads(response)
            tournaments = tournament_data.get("tournaments", [])
            if not tournaments:
                continue

            tournaments_by_month[calendar.month_name[month]].extend(tournaments)
        except json.JSONDecodeError:
            continue

    return tournaments_by_month


async def get_matches_by_month_with_pw(base_url: str) -> None:
    base_match_url, base_data_url, league_name = parse_base_url(base_url)

    tournaments = await get_tournaments_by_month_by_pw(base_data_url)
    match_urls = find_matches_url_by_tournaments(
        tournaments,
        base_match_url,
        league_name,
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)  # Limit concurrent tasks

        async def scrape_url(url: str, path: str, tqdm_bar) -> None:
            async with semaphore:
                page = await browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                await fetch_page_content(page, url, path)
                await page.close()
                tqdm_bar.update(1)

        file_paths = []
        tasks = []
        # Initialize tqdm progress bar
        with tqdm(
            total=len(match_urls),
            desc="Scraping Matches",
            unit="url",
        ) as progress_bar:
            for match_url in match_urls:
                month = match_url.split("x-month=")[1]
                match_id = match_url.split("/")[4]

                save_path = f"matches/{league_name}/{month}/raw_html_{match_id}.html"
                file_paths.append(save_path)
                tasks.append(scrape_url(match_url, save_path, progress_bar))

            await asyncio.gather(*tasks)
        await browser.close()

    for file_path in tqdm(file_paths, desc="Parsing playwright data"):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            month = file_path.split("/")[2]
            parse_match_html(content, month, league_name)


async def find_valid_urls_with_pw(tournament_urls: list[str]) -> None:
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

    responses = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        async with semaphore:
            for url in tqdm(tournament_urls, desc="Finding valid URLs"):
                page = await browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                response = await fetch_page_content(page, url, None, save_file=False)
                responses.append(response)
                await page.close()

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

    await browser.close()


async def update_matches_by_recent_matches_with_pw() -> None:
    now = time.localtime()
    month = now.tm_mon
    month_name = calendar.month_name[month]
    day = now.tm_mday

    today_url = f"https://www.whoscored.com/livescores/data?d=2024{month:02d}{day:02d}&isSummary=true"
    yesterday_url = f"https://www.whoscored.com/livescores/data?d=2024{month:02d}{day - 1:02d}&isSummary=true"

    responses = []
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for url in [today_url, yesterday_url]:
            page = await browser.new_page()
            await page.set_extra_http_headers(HEADERS)
            content = await fetch_page_content(page, url, None, save_file=False)
            content = content.replace("</body></html>", "").replace(
                "<html><head></head><body>", ""
            )
            responses.append(json.loads(content))
            await page.close()
        await browser.close()

    with open("matches/all_regions.json", "r", encoding="utf-8") as file:
        region_data = json.load(file)

    tournament_name_league_mapping = {}
    for region in region_data:
        for league in region["tournaments"]:
            key = f"{region['id']}_{league['id']}"
            tournament_name_league_mapping[key] = (
                "https://www.whoscored.com" + league["url"]
            )

    tournaments = []
    base_tournament_urls = []
    for response, day in zip(responses, [day, day - 1]):
        for tournament in response["tournaments"]:
            tournament["x-day"] = day
            tournaments.append(tournament)
            base_tournament_urls.append(
                tournament_name_league_mapping[
                    f"{tournament['regionId']}_{tournament['tournamentId']}"
                ]
            )

    await find_valid_urls_with_pw(base_tournament_urls)

    with open("matches/tournament_url_mapping.json", "r", encoding="utf-8") as f:
        tournament_url_mapping = json.load(f)
    match_url_by_league = defaultdict(list)

    for tournament in tournaments:
        league_name = tournament_url_mapping[
            tournament_name_league_mapping[
                f"{tournament['regionId']}_{tournament['tournamentId']}"
            ]
        ].split("/")[-1]
        os.makedirs(f"matches/{league_name}/{month_name}", exist_ok=True)
        match_day = tournament["x-day"]
        write_file(
            f"matches/{league_name}/{month_name}/matches_{match_day:02d}.json",
            [tournament],
            is_json=True,
        )

        base_url = f"https://www.whoscored.com/Matches/{{match_id}}/Live/{league_name}-{{home_team}}-{{away_team}}"
        for match in tournament["matches"]:
            home_team = match["homeTeamName"].replace(" ", "-").replace(".", "")
            away_team = match["awayTeamName"].replace(" ", "-").replace(".", "")
            match_url = base_url.format(
                match_id=match["id"], home_team=home_team, away_team=away_team
            )

            match_url_by_league[league_name].append(match_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def scrape_and_save_content(url: str, path: str, tqdm_bar) -> None:
            async with semaphore:
                page = await browser.new_page()
                await page.set_extra_http_headers(HEADERS)
                page_content = await fetch_page_content(page, url, path)
                if page_content:
                    write_file(save_path, page_content)
                await page.close()
                tqdm_bar.update(1)

        tasks = []
        with tqdm(
            total=len(match_url_by_league.values()),
            desc="Scraping Matches",
            unit="url",
        ) as progress_bar:
            for league_name, urls in match_url_by_league.items():
                for url in urls:
                    match_id = url.split("/")[4]
                    save_path = (
                        f"matches/{league_name}/{month_name}/raw_html_{match_id}.html"
                    )
                    tasks.append(scrape_and_save_content(url, save_path, progress_bar))

            await asyncio.gather(*tasks)
        await browser.close()

    for league_name, urls in tqdm(
        match_url_by_league.items(),
        desc="Fetching matches...",
    ):
        for url in urls:
            match_id = url.split("/")[4]
            file_path = f"matches/{league_name}/{month_name}/raw_html_{match_id}.html"
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                parse_match_html(content, month_name, league_name)
