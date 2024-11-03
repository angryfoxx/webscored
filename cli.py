import asyncio
import json
import os
import random

import asyncclick as click
import pydash
from alembic import command
from alembic.config import Config

from constants import DATABASE_URI
from logger import logger
from populate import populate_incident_events
from scraper import fetch_base_data, get_matches_by_month
from utils import find_valid_urls


def find_possible_regions(search_term):
    return pydash.filter_(REGIONS, lambda region: search_term.lower() in region.lower())


def display_regions(regions):
    regions = regions[:5]
    for i, region in enumerate(regions, start=1):
        click.echo(f"\033[96m{i}. {region}\033[0m")

    click.echo()


async def scrape_url(url: str, playwright: bool = False):
    """Runs the scraping function asynchronously to fetch matches by month."""

    click.echo("\033[93mFetching matches...\033[0m")
    if playwright:
        # TODO: Implement Playwright scraping
        ...
    else:
        await get_matches_by_month(url)

    click.echo(
        "\033[92mFetching matches completed! You can find the matches in the matches folder.\033[0m"
    )


def find_tournament_url(all_leagues) -> list[str]:
    while True:
        # default to 5 random regions
        selected_regions = random.sample(REGIONS, 5)

        search_term = click.prompt(
            "\033[94mEnter country name to search or press Enter to select from the list\033[0m",
            default="",
            show_default=False,
        )

        if search_term:
            selected_regions = find_possible_regions(search_term)
            if not selected_regions:
                click.echo("\033[91mNo regions found. Please try again.\033[0m")
                continue

        display_regions(selected_regions)

        try:
            region_choice = int(click.prompt("\033[94mEnter the region number\033[0m"))
            if region_choice < 1 or region_choice > len(selected_regions):
                click.echo("\033[91mInvalid choice. Please try again.\033[0m\n")
                continue
        except ValueError:
            click.echo("\033[91mInvalid choice. Please try again.\033[0m\n")
            continue

        click.echo(
            f"\033[92mSelected region: {selected_regions[region_choice - 1]}\033[0m\n"
        )

        selected_region_data = pydash.find(
            REGION_DATA,
            lambda region: region["name"] == selected_regions[region_choice - 1],
        )

        if all_leagues:
            click.echo("\033[92mSelected all leagues.\033[0m")
            league_urls = [
                f"https://www.whoscored.com{league['url']}"
                for league in selected_region_data.get("tournaments", [])
            ]
            return league_urls

        # Select League within Region
        click.echo("\033[94mSelect a league:\033[0m")
        leagues = selected_region_data.get("tournaments", [])
        for i, league in enumerate(leagues, start=1):
            click.echo(f"\033[96m{i}. {league['name']}\033[0m")
        click.echo()

        league_choice = click.prompt("\033[94mEnter the league number\033[0m", type=int)
        if league_choice < 1 or league_choice > len(leagues):
            click.echo("\033[91mInvalid choice. Please try again.\033[0m\n")
            continue

        selected_league = leagues[league_choice - 1]
        click.echo(f"\033[92mSelected league: {selected_league['name']}\033[0m")

        league_url = f"https://www.whoscored.com{selected_league['url']}"
        return [league_url]


def get_all_tournaments_urls():
    urls = []
    for region in REGION_DATA:
        for league in region["tournaments"]:
            urls.append(f"https://www.whoscored.com{league['url']}")
    return urls


def get_urls(tournament_urls):
    with open("matches/tournament_url_mapping.json", "r", encoding="utf-8") as f:
        tournament_url_mapping = json.load(f)
    urls = [tournament_url_mapping[url] for url in tournament_urls]
    return urls


@click.command()
@click.option(
    "--fetch-all",
    "-fa",
    is_flag=True,
    help="Select all regions.",
)
@click.option(
    "--all-leagues",
    "-al",
    is_flag=True,
    help="Select all leagues.",
)
@click.option(
    "--playwright",
    "-pw",
    is_flag=True,
    help="Use Playwright for scraping.",
)
@click.option(
    "populate",
    "--populate",
    "-p",
    is_flag=True,
    help="Populate the database from a JSON file.",
)
@click.option(
    "scrape",
    "--scrape",
    "-s",
    is_flag=True,
    help="Scrape data from an external source.",
)
@click.option(
    "run",
    "--run",
    "-r",
    is_flag=True,
    help="Execute both scrape and populate in order.",
)
async def cli(fetch_all, all_leagues, playwright, populate, scrape, run):
    if populate:
        populate_incident_events()
        click.echo("\033[92mDatabase populated successfully!\033[0m")
        return

    base_urls = (
        get_all_tournaments_urls() if fetch_all else find_tournament_url(all_leagues)
    )

    await find_valid_urls(base_urls)
    urls = get_urls(base_urls)

    if scrape:
        for url in urls:
            click.echo(f"\033[93mScraping data from {url}...\033[0m")
            logger.info(f"Scraping data from {url}")
            await scrape_url(url, playwright)
    elif run:
        for url in urls:
            click.echo(f"\033[93mScraping data from {url}...\033[0m")
            logger.info(f"Scraping data from {url}")
            await scrape_url(url, playwright)
        populate_incident_events()
    else:
        click.echo("\033[91mPlease select an option.\033[0m")


def database_exists():
    if DATABASE_URI.startswith("sqlite:///"):
        # For SQLite, check if the database file exists
        db_path = DATABASE_URI.replace("sqlite:///", "")
        return os.path.exists(db_path)
    else:
        # For other databases, attempt to connect
        from sqlalchemy import create_engine

        engine = create_engine(DATABASE_URI)
        try:
            with engine.connect():
                return True
        except Exception:
            return False


def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def init_db():
    """Initialize the database and apply migrations if needed."""
    if database_exists():
        logger.info("Database already exists. Applying migrations...")
    else:
        logger.info(
            "Database does not exist. Creating database and applying migrations..."
        )

    apply_migrations()
    click.echo("Database is up-to-date with latest migrations.")


if __name__ == "__main__":
    if not os.path.exists("matches"):
        os.makedirs("matches")

    if not os.path.exists("matches/all_regions.json"):
        click.echo("\033[93mBase data not found. Fetching base data...\033[0m")
        fetch_base_data()
        click.echo("\033[92mBase data fetched successfully!\033[0m")

    with open("matches/all_regions.json", "r", encoding="utf-8") as file:
        REGION_DATA = json.load(file)

    REGIONS = [region["name"] for region in REGION_DATA]

    init_db()

    asyncio.run(cli())
