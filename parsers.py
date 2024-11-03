import json
import os

from bs4 import BeautifulSoup

from utils import write_file


def parse_match_html(html_content: str, month: str, league_name: str) -> None:
    # Parse the HTML
    soup = BeautifulSoup(html_content, "lxml")

    # there is json in scripts with this name require.config.params["args"]
    scripts = soup.find_all("script")

    data_script = next(
        filter(lambda tag: 'require.config.params["args"]' in tag.text, scripts), None
    )
    if not data_script:
        return None

    json_str = data_script.text[
        data_script.text.find("{") : data_script.text.rfind("}") + 1
    ]
    match_id = (
        json_str[json_str.find("matchId") : json_str.find(",")]
        .replace(" ", "")
        .split(":")[-1]
    )

    if "matchCentreData" not in json_str:
        print(
            f"\033[91mNo 'match centre data' found for match {match_id}. Month: {month} League: {league_name}\033[0m"
        )
        return None

    json_str = (
        json_str.replace("\n", "")
        .replace("matchCentreData", '"matchCentreData"')
        .replace("matchId", '"matchId"')
        .replace("matchCentreEventTypeJson", '"matchCentreEventTypeJson"')
        .replace("formationIdNameMappings", '"formationIdNameMappings"')
        .replace("initialMatchDataForScrappers", '"initialMatchDataForScrappers"')
        .replace("hasLineup", '"hasLineup"')
    )
    # Parse the corrected JSON string
    json_data = json.loads(json_str)

    if match_centre_data := json_data.get("matchCentreData"):
        write_file(
            f"matches/{league_name}/{month}/match_centre_data_{match_id}.json",
            match_centre_data,
            is_json=True,
        )

    if not os.path.exists(
        f"matches/{league_name}/{month}/formation_id_name_mappings.json"
    ):
        write_file(
            f"matches/{league_name}/{month}/formation_id_name_mappings.json",
            json_data["formationIdNameMappings"],
            is_json=True,
        )

    if not os.path.exists(
        f"matches/{league_name}/{month}/match_centre_event_type.json"
    ):
        write_file(
            f"matches/{league_name}/{month}/match_centre_event_type.json",
            json_data["matchCentreEventTypeJson"],
            is_json=True,
        )


def parse_base_data(html_content: str) -> None:
    soup = BeautifulSoup(html_content, "lxml")
    scripts = soup.find_all("script")
    regions = next(filter(lambda tag: "var allRegions" in tag.text, scripts), None)

    if not regions:
        return

    regions_str = regions.text[regions.text.find("[") : regions.text.rfind("]") + 1]
    regions_str = (
        regions_str.replace("\n", "")
        .replace("'", '"')
        .replace("type:", '"type":')
        .replace("id:", '"id":')
        .replace("flg:", '"flg":')
        .replace("name:", '"name":')
        .replace("tournaments:", '"tournaments":')
        .replace("url:", '"url":')
        .replace("sortOrder:", '"sortOrder":')
    )
    regions_json = json.loads(regions_str)

    write_file(
        "matches/all_regions.json",
        regions_json,
        is_json=True,
    )


def parse_base_url(base_url: str) -> tuple[str, str, str]:
    league_name = base_url.split("/")[-1]
    stage_id = base_url.split("/")[-3]

    data_url = f"https://www.whoscored.com/tournaments/{stage_id}/data/?d=2024{{month:02d}}&isAggregate=false"
    # x-month is used to indicate the month of the match in the URL for development purposes.
    match_url = f"https://www.whoscored.com/Matches/{{match_id}}/Live/{league_name}-{{home_team}}-{{away_team}}?x-month={{month}}"

    return match_url, data_url, league_name
