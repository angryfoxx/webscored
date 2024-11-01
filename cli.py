import argparse
import asyncio

from populate import populate_incident_events
from scraper import get_matches_by_month


async def scrape():
    """Runs the scraping function asynchronously to fetch matches by month."""

    print("\033[93mFetching matches...\033[0m")

    await get_matches_by_month()

    print(
        "\033[92mFetching matches completed! You can find the matches in the matches folder."
    )


def main():
    parser = argparse.ArgumentParser(
        description="CLI for populating, scraping, and running both tasks."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("populate", help="Populate the database from a JSON file.")
    subparsers.add_parser("scrape", help="Scrape data from an external source.")
    subparsers.add_parser("run", help="Execute both scrape and populate in order.")

    args = parser.parse_args()

    if args.command == "populate":
        populate_incident_events()
    elif args.command == "scrape":
        asyncio.run(scrape())
    elif args.command == "run":
        # Run scrape first, then populate
        asyncio.run(scrape())
        populate_incident_events()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
