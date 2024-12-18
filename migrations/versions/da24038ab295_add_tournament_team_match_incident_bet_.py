"""add tournament, team, match, incident, bet table

Revision ID: da24038ab295
Revises: 271fa542eb94
Create Date: 2024-11-03 15:44:42.367727

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "da24038ab295"
down_revision: Union[str, None] = "271fa542eb94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("country_code", sa.String(), nullable=True),
        sa.Column("country_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("season_name", sa.String(), nullable=True),
        sa.Column("region_name", sa.String(), nullable=True),
        sa.Column("region_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stage_id", sa.Integer(), nullable=True),
        sa.Column("tournament_id", sa.Integer(), nullable=True),
        sa.Column("home_team_id", sa.Integer(), nullable=True),
        sa.Column("away_team_id", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("period", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["away_team_id"],
            ["teams.id"],
        ),
        sa.ForeignKeyConstraint(
            ["home_team_id"],
            ["teams.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "bets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("bet_name", sa.String(), nullable=True),
        sa.Column("odds_decimal", sa.Float(), nullable=True),
        sa.Column("odds_fractional", sa.String(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=True),
        sa.Column("click_out_url", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("minute", sa.Integer(), nullable=True),
        sa.Column("type", sa.Integer(), nullable=True),
        sa.Column("sub_type", sa.Integer(), nullable=True),
        sa.Column("player_name", sa.String(), nullable=True),
        sa.Column("participating_player_name", sa.String(), nullable=True),
        sa.Column("field", sa.Integer(), nullable=True),
        sa.Column("period", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["matches.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("incidents")
    op.drop_table("bets")
    op.drop_table("matches")
    op.drop_table("tournaments")
    op.drop_table("teams")
    # ### end Alembic commands ###
