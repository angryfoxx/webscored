from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class IncidentEvent(Base):
    __tablename__ = "incident_event"
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    match_id = Column(Integer)
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


class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    season_name = Column(String)
    region_name = Column(String)
    region_id = Column(Integer)

    matches = relationship("Match", back_populates="tournament")


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_code = Column(String)
    country_name = Column(String)


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    start_time = Column(DateTime)
    status = Column(Integer)
    home_score = Column(Integer)
    away_score = Column(Integer)
    period = Column(Integer)

    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    tournament = relationship("Tournament", back_populates="matches")
    incidents = relationship("Incident", back_populates="match")


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    minute = Column(Integer)
    type = Column(Integer)
    sub_type = Column(Integer)
    player_name = Column(String)
    participating_player_name = Column(String)
    field = Column(Integer)
    period = Column(Integer)

    match = relationship("Match", back_populates="incidents")


class Bet(Base):
    __tablename__ = "bets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    bet_name = Column(String)
    odds_decimal = Column(Float)
    odds_fractional = Column(String)
    provider_id = Column(Integer)
    click_out_url = Column(String)

    match = relationship("Match")
