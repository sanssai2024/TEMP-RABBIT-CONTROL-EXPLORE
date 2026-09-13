"""initial schema

Revision ID: 20260911_0001
Revises: 
Create Date: 2026-09-11 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260911_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ideas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_idea", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("current_decision", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ideas_id"), "ideas", ["id"], unique=False)

    op.create_table(
        "idea_processings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("structured_result_json", sa.JSON(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=True),
        sa.Column("next_action", sa.String(length=500), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_idea_processings_id"), "idea_processings", ["id"], unique=False)
    op.create_index(op.f("ix_idea_processings_idea_id"), "idea_processings", ["idea_id"], unique=False)

    op.create_table(
        "idea_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("idea_id", sa.Integer(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["idea_id"], ["ideas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_idea_notes_id"), "idea_notes", ["id"], unique=False)
    op.create_index(op.f("ix_idea_notes_idea_id"), "idea_notes", ["idea_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_idea_notes_idea_id"), table_name="idea_notes")
    op.drop_index(op.f("ix_idea_notes_id"), table_name="idea_notes")
    op.drop_table("idea_notes")

    op.drop_index(op.f("ix_idea_processings_idea_id"), table_name="idea_processings")
    op.drop_index(op.f("ix_idea_processings_id"), table_name="idea_processings")
    op.drop_table("idea_processings")

    op.drop_index(op.f("ix_ideas_id"), table_name="ideas")
    op.drop_table("ideas")
