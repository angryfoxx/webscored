from sqlalchemy import JSON, Boolean, Column, Float, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class IncidentEvent(Base):
    __tablename__ = "incident_event"
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    event_id = Column(Integer)
    minute = Column(Integer)
    second = Column(Integer)
    team_id = Column(Integer)
    player_id = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    expanded_minute = Column(Integer)
    period_value = Column(Integer)
    period_display_name = Column(String)
    type_value = Column(Integer)
    type_display_name = Column(String)
    outcome_type_value = Column(Integer)
    outcome_type_display_name = Column(String)
    qualifiers = Column(JSON)
    satisfied_events_types = Column(JSON)
    is_touch = Column(Boolean)
    end_x = Column(Float)
    end_y = Column(Float)
    goal_mouth_x = Column(Float)
    goal_mouth_y = Column(Float)
    related_event_id = Column(Integer)
    related_player_id = Column(Integer)
    card_type_value = Column(Integer)
    card_type_display_name = Column(String)
    is_goal = Column(Boolean, default=False)
    is_shot = Column(Boolean, default=False)
