import json

from bs4 import BeautifulSoup

from utils import write_file


def parse_match_html(html_content: str, month: str) -> None:
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

    json_str = (
        json_str.replace("\n", "")
        .replace("matchCentreData", '"matchCentreData"')
        .replace("matchId", '"matchId"')
        .replace("matchCentreEventTypeJson", '"matchCentreEventTypeJson"')
        .replace("formationIdNameMappings", '"formationIdNameMappings"')
    )
    # Parse the corrected JSON string
    json_data = json.loads(json_str)

    # matchId, matchCentreData, matchCentreEventTypeJson, formationIdNameMappings
    match_id = json_data["matchId"]

    regions = next(filter(lambda tag: "var allRegions" in tag.text, scripts), None)

    if regions:
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
            f"matches/{month}/regions_{match_id}.json", regions_json, is_json=True
        )

    write_file(
        f"matches/{month}/formation_id_name_mappings_{match_id}.json",
        json_data["formationIdNameMappings"],
        is_json=True,
    )

    if match_centre_data := json_data.get("matchCentreData"):
        write_file(
            f"matches/{month}/match_centre_data_{match_id}.json",
            match_centre_data,
            is_json=True,
        )
    else:
        print(f"\033[91mNo 'match centre data' found for match {match_id}\033[0m")

    write_file(
        f"matches/{month}/match_centre_event_type_{match_id}.json",
        json_data["matchCentreEventTypeJson"],
        is_json=True,
    )
