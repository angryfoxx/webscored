import json

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm

from constants import DATABASE_URI
from models import Base, IncidentEvent
from utils import find_match_files


def populate_incident_events():
    json_files = find_match_files()
    if not json_files:
        print(
            "\033[91mNo JSON files found in the matches folder. Please scrape data first.\033[0m"
        )
        return

    print("\033[93mPopulating incident events...\033[0m")
    print(f"\033[93m{len(json_files)} files found\033[0m")

    engine = create_engine(DATABASE_URI)
    print("\033[93mConnected to the database!\033[0m")

    Session = sessionmaker(bind=engine)
    session = Session()

    if not inspect(engine).has_table("incident_event"):
        Base.metadata.create_all(engine)

    incident_events = []
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                continue
            if not data:
                continue

            incident_events.extend(data.get("home", {}).get("incidentEvents", []))
            incident_events.extend(data.get("away", {}).get("incidentEvents", []))

    existing_incident_event_ids = set(
        ie_id for ie_id, in session.query(IncidentEvent.id).all()
    )

    for event in tqdm(incident_events, desc="Populating incident events"):
        idx = int(event.get("id"))
        if idx in existing_incident_event_ids:
            continue

        incident_event = IncidentEvent(
            id=idx,
            event_id=event.get("eventId"),
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
            outcome_type_display_name=event.get("outcomeType", {}).get("displayName"),
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

        session.add(incident_event)

    session.commit()
    print("\033[92mIncident events have been populated successfully!\033[0m")
