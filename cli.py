import argparse
import asyncio
import re

from populate import populate_incident_events
from scraper import get_matches_by_month


async def scrape(url: str):
    """Runs the scraping function asynchronously to fetch matches by month."""

    print("\033[93mFetching matches...\033[0m")

    await get_matches_by_month(url)

    print(
        "\033[92mFetching matches completed! You can find the matches in the matches folder."
    )


def validate_url(url: str) -> None:
    """Validates the URL to ensure it is a valid URL."""

    pattern = r"^https://www\.whoscored\.com/Regions/\d+/Tournaments/\d+/Seasons/\d+/Stages/\d+/Fixtures/[^/]+$"
    if not re.match(pattern, url):
        raise argparse.ArgumentTypeError(
            "Invalid URL. Please provide a valid URL."
            " Example: https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/10316/Stages/23400/Fixtures/England-Premier-League-2024-2025"
        )


def main():
    parser = argparse.ArgumentParser(
        description="CLI for populating, scraping, and running both tasks."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("populate", help="Populate the database from a JSON file.")
    scrape_parser = subparsers.add_parser(
        "scrape", help="Scrape data from an external source."
    )
    scrape_parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL to fetch matches from.",
    )
    run_parser = subparsers.add_parser(
        "run", help="Execute both scrape and populate in order."
    )
    run_parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL to fetch matches from.",
    )

    args = parser.parse_args()

    url = getattr(args, "url", None)
    if url:
        validate_url(url)

    if args.command == "populate":
        populate_incident_events()
    elif args.command == "scrape":
        asyncio.run(scrape(url))
    elif args.command == "run":
        # Run scrape first, then populate
        asyncio.run(scrape(url))
        populate_incident_events()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
