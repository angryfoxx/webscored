[example output](https://github.com/angryfoxx/webscored/blob/main/assets/example_output.png)

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

- `populate`: Populate match data from a JSON file.
- `scrape`: Scrape match data from external sources.
- `run`: Run both tasks in sequence.

To run a command, use the following syntax:

```bash
python cli.py <command>
```

## Scraping Data

The `scrape` command allows you to scrape match data from external sources.
And writes it to matches folder in this structure:
```
matches
├── November
│   ├── matches.json
│   ├── raw_html_<match_id>.html
│   ├── match_centre_event_type_<match_id>.json
│   ├── match_centre_data_<match_id>.json
│   ├── formation_id_name_mapppings_<match_id>.json
│   ├── regions_<match_id>.json
│   └── ...
├── December
├── ...
```

## Populating Data

The `populate` command allows you to populate match data from a JSON file. 
And writes it to matches.db file.
