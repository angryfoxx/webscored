![example output](https://github.com/angryfoxx/webscored/blob/main/assets/example_output.png?raw=true)

# Match Data CLI

This project provides a command-line interface (CLI) to manage match data, allowing you to populate data from a JSON file, scrape data from external sources, and run both tasks in sequence.

## Setup

### 1. Create a Virtual Environment

To keep dependencies isolated, create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
```

### 2. Install Dependencies

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the CLI

Run the CLI with the following command:

```bash
python cli.py
```

## Usage

The CLI provides the following commands:

- `--populate`or `-p`: Populate match data from a JSON file.
- `--scrape` or `-s`: Scrape match data from external sources.
- `--run` or `-r`: Run both tasks in sequence.
- `--fetch-recent` or `-fr`: Fetch recent matches for the selected region.

And the following options:

- `--help`: Display help information for the command.
- `--fetch-all` or `-fa`: Fetch all matches for the selected region.
- `--all-leagues` or `-al`: Fetch all leagues for the selected region.
- `--playwright` or `-pw`: Use Playwright to scrape data. This option is available for the `scrape`, `run`, and `fetch-recent` commands.
Do not forget to install Playwright dependencies if you want to use this option.
```
playwright install
```

To run a command, use the following syntax:

```bash
python cli.py <command>
```

If you don't provide a option, the CLI will prompt you to select region and league.

## Scraping Data

The `scrape` command allows you to scrape match data from external sources.
And writes it to matches folder in this structure:
```
matches
├── England-Premier-League-2024-2025
│   ├── November
│   │   ├── matches.json
│   │   ├── raw_html_<match_id>.html
│   │   ├── match_centre_event_type.json
│   │   ├── match_centre_data_<match_id>.json
│   │   ├── formation_id_name_mapppings.json
│   │   └── ...
│   ├── December
│   │   └── ...
│   └── ...
├── England-League-One-2024-2025
│   └── ...
├── tournament_url_mapping.json
├── all_regions.json
└── ...
```

all_regions, formation_id_name_mapppings, match_centre_event_type does not have a specific structure.
Because it is same for all leagues and regions.

## Populating Data

The `populate` command allows you to populate match data from a JSON file. 
And writes it to matches.db file.
Or you can change the database by set the DATABASE_URI environment variable.
