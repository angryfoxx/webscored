import json
from datetime import datetime

from tqdm import tqdm

from database import SessionLocal
from logger import logger
from models import Bet, Incident, IncidentEvent, Match, Team, Tournament
from utils import find_incident_event_files, find_match_files


def populate_incident_events():
    logger.info("Populating incident events...")

    json_files = find_incident_event_files()
    if not json_files:
        logger.error(
            "No JSON files found in the matches folder. Please scrape data first."
        )
        return

    logger.info(f"{len(json_files)} incident event files found.")

    session = SessionLocal()

    # Get existing incident event IDs to avoid duplicates
    existing_incident_event_ids = set(
        ie_id for ie_id, in session.query(IncidentEvent.id).all()
    )
    logger.info(
        f"{len(existing_incident_event_ids)} existing incident events found. Skipping duplicates..."
    )

    new_incident_events = []

    for json_file in tqdm(json_files, desc="Populating incident events"):
        with open(json_file, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to load {json_file}: {e}")
                continue

            incident_events = data.get("home", {}).get("incidentEvents", []) + data.get(
                "away", {}
            ).get("incidentEvents", [])

        match_id = json_file.split("_")[-1].split(".")[0]

        for event in incident_events:
            idx = int(event.get("id"))
            if idx in existing_incident_event_ids:
                continue

            incident_event = IncidentEvent(
                id=idx,
                event_id=event.get("eventId"),
                match_id=match_id,
                minute=event.get("minute"),
                second=event.get("second"),
                team_id=event.get("teamId"),
                player_id=event.get("playerId"),
                x=event.get("x"),
                y=event.get("y"),
                expanded_minute=event.get("expandedMinute"),
                period_value=event.get("period", {}).get("value"),
                period_display_name=event.get("period", {}).get("displayName"),
                type_value=event.get("type", {}).get("value"),
                type_display_name=event.get("type", {}).get("displayName"),
                outcome_type_value=event.get("outcomeType", {}).get("value"),
                outcome_type_display_name=event.get("outcomeType", {}).get(
                    "displayName"
                ),
                qualifiers=event.get("qualifiers", []),
                satisfied_events_types=event.get("satisfiedEventsTypes", []),
                is_touch=event.get("isTouch", False),
                end_x=event.get("endX"),
                end_y=event.get("endY"),
                goal_mouth_x=event.get("goalMouthX"),
                goal_mouth_y=event.get("goalMouthY"),
                related_event_id=event.get("relatedEventId"),
                related_player_id=event.get("relatedPlayerId"),
                card_type_value=event.get("cardType", {}).get("value"),
                card_type_display_name=event.get("cardType", {}).get("displayName"),
                is_goal=event.get("isGoal", False),
                is_shot=event.get("isShot", False),
            )

            new_incident_events.append(incident_event)
            existing_incident_event_ids.add(idx)

        # Commit in batches of 1000 to optimize database interaction
        if len(new_incident_events) >= 1000:
            session.bulk_save_objects(new_incident_events)
            session.commit()
            new_incident_events.clear()

    if new_incident_events:
        session.bulk_save_objects(new_incident_events)
        session.commit()

    logger.info("Incident events have been populated successfully!")


def load_data():
    logger.info("Population matches data...")

    json_files = find_match_files()
    data = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            try:
                json_data = json.load(file)
                data.extend(json_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to load {json_file}: {e}")
                continue

    logger.info(f"{len(data)} files found")

    # Preprocess data to collect all records
    tournaments = {}
    teams = {}
    matches = []
    incidents = []
    bets = []

    session = SessionLocal()
    existing_tournament_ids = set(t_id for t_id, in session.query(Tournament.id).all())
    existing_match_ids = set(m_id for m_id, in session.query(Match.id).all())
    existing_team_ids = set(t_id for t_id, in session.query(Team.id).all())

    logger.info(
        f"{len(existing_tournament_ids)} existing tournaments found. Skipping duplicates..."
    )
    logger.info(
        f"{len(existing_match_ids)} existing matches found. Skipping duplicates..."
    )
    logger.info(
        f"{len(existing_team_ids)} existing teams found. Skipping duplicates..."
    )

    for tournament_data in tqdm(data, desc="Loading matches..."):
        # Collect tournaments
        tournament_id = tournament_data["tournamentId"]
        if (
            tournament_id not in tournaments
            and tournament_id not in existing_tournament_ids
        ):
            tournaments[tournament_id] = Tournament(
                id=tournament_id,
                name=tournament_data["tournamentName"],
                season_name=tournament_data["seasonName"],
                region_name=tournament_data["regionName"],
                region_id=tournament_data["regionId"],
            )

        for match_data in tournament_data["matches"]:
            match_id = match_data["id"]
            if match_id in existing_match_ids:
                continue

            existing_match_ids.add(match_id)

            # Collect teams
            home_team_id = match_data["homeTeamId"]
            if home_team_id not in existing_team_ids:
                teams[home_team_id] = Team(
                    id=home_team_id,
                    name=match_data["homeTeamName"],
                    country_code=match_data["homeTeamCountryCode"],
                    country_name=match_data["homeTeamCountryName"],
                )
                existing_team_ids.add(home_team_id)

            away_team_id = match_data["awayTeamId"]
            if away_team_id not in existing_team_ids:
                teams[away_team_id] = Team(
                    id=away_team_id,
                    name=match_data["awayTeamName"],
                    country_code=match_data["awayTeamCountryCode"],
                    country_name=match_data["awayTeamCountryName"],
                )
                existing_team_ids.add(away_team_id)

            # Collect matches
            match = Match(
                id=match_id,
                stage_id=match_data["stageId"],
                tournament_id=tournament_id,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                start_time=datetime.fromisoformat(
                    match_data["startTimeUtc"].replace("Z", "+00:00")
                ),
                status=match_data["status"],
                home_score=match_data["homeScore"],
                away_score=match_data["awayScore"],
                period=match_data["period"],
            )
            matches.append(match)

            # Collect incidents
            for incident_data in match_data.get("incidents", []) or []:
                incident = Incident(
                    match_id=match_id,
                    minute=int(incident_data["minute"]),
                    type=incident_data["type"],
                    sub_type=incident_data["subType"],
                    player_name=incident_data["playerName"],
                    participating_player_name=incident_data.get(
                        "participatingPlayerName"
                    ),
                    field=incident_data["field"],
                    period=incident_data["period"],
                )
                incidents.append(incident)

            # Collect bets
            bets_data = match_data.get("bets", {}) or {}
            for bet_type, bet_data in bets_data.items():
                if not bet_data:
                    continue

                offers = bet_data.get("offers", []) or []
                for offer in offers:
                    bet = Bet(
                        match_id=match_id,
                        bet_name=bet_data["betName"],
                        odds_decimal=float(offer["oddsDecimal"]),
                        odds_fractional=offer["oddsFractional"],
                        provider_id=offer["providerId"],
                        click_out_url=offer["clickOutUrl"],
                    )
                    bets.append(bet)

    # Bulk insert all records
    session.bulk_save_objects(tournaments.values())
    session.bulk_save_objects(teams.values())
    session.bulk_save_objects(matches)
    session.bulk_save_objects(incidents)
    session.bulk_save_objects(bets)
    session.commit()
    logger.info("Data has been loaded successfully!")


def populate_data():
    logger.info("Starting data population...")
    load_data()
    populate_incident_events()
    logger.info("Data population has been completed successfully!")
