"""create_main_tables
Revision ID: 9bf7d5cb7916
Revises: 77ab2fcbd4a6
Create Date: 2021-04-07 20:19:48.420665
"""
from typing import Tuple

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision = "9bf7d5cb7916"

down_revision = None
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
    )


def create_todos_table() -> None:
    op.create_table(
        "todos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.Text, nullable=False, index=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("priority", sa.Text, nullable=False, server_default="high"),
        sa.Column("duedate", sa.Date, nullable=False, index=True),
        sa.Column("owner", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("as_task", sa.Boolean(), nullable=False, server_default="False"),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_todos_modtime
            BEFORE UPDATE
            ON todos
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("password", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="True"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="False"),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_user_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


def create_profle_table() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        # sa.Column("full_name", sa.Text, nullable=True),
        sa.Column("firstname", sa.Text, nullable=True),
        sa.Column("lastname", sa.Text, nullable=True),
        sa.Column("middlename", sa.Text, nullable=True),
        sa.Column("phone_number", sa.Text, nullable=True),
        sa.Column("bio", sa.Text, nullable=True, server_default=""),
        sa.Column("image", sa.Text, nullable=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_profiles_modtime
            BEFORE UPDATE
            ON profiles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


def create_note_table() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("notes_summary", sa.Text, nullable=True),
        sa.Column("todo_id", sa.Integer, sa.ForeignKey("todos.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_notes_modtime
            BEFORE UPDATE
            ON notes
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


# def create_email_verification_table() -> None:
#     op.create_table(
#         "email_verification",
#         sa.Column("generated_code", sa.Text, nullable=False, index=True),
#         sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
#         *timestamps(),
#     )
#     op.create_primary_key("pk_email_verification", "email_verification", ["generated_code", "user_id"])
#     op.execute(
#         """
#         CREATE TRIGGER update_email_modtime
#             BEFORE UPDATE
#             ON email_verification
#             FOR EACH ROW
#         EXECUTE PROCEDURE update_updated_at_column()
#         """
#     )


def create_commment_table() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("body", sa.Text, nullable=True, server_default=""),
        sa.Column("todo_id", sa.Integer, sa.ForeignKey("todos.id", ondelete="CASCADE")),
        sa.Column("comment_owner", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("task", sa.Boolean, nullable=True, server_default="False"),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_comments_modtime
            BEFORE UPDATE
            ON comments
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


def create_task_offer_table() -> None:
    op.create_table(
        "user_task_for_todos",
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "todo_id",
            sa.Integer,
            sa.ForeignKey("todos.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.Text, nullable=False, server_default="pending", index=True),
        *timestamps(),
    )
    op.create_primary_key("pk_user_task_for_todos", "user_task_for_todos", ["user_id", "todo_id"])
    op.execute(
        """
        CREATE TRIGGER update_user_task_for_todos_modtime
            BEFORE UPDATE
            ON user_task_for_todos
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


def create_task_taker_evaluations_table() -> None:
    """
    Owner of a task (i.e. todo offered) should be able to evauluate the task taker's execution of the job.
    - Allow owner to leave ratings, headline and comments.
    - Add no show if the task was not done.
    - Rating splits into sections
        - professionalism - did they handle thinks likle pros?
        - completeness - how through were they? did every detail needed in the task executed.
        - efficiency - how quickly and effectively did they get the task done?
        - overall - what's the rating for the task executed?
    """
    op.create_table(
        "task_to_tasktaker_evalations",
        sa.Column(
            "todo_id",
            sa.Integer,
            sa.ForeignKey("todos.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tasktaker_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column("no_show", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("headline", sa.Text, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("professionalism", sa.Integer, nullable=True),
        sa.Column("completeness", sa.Integer, nullable=True),
        sa.Column("efficiency", sa.Integer, nullable=True),
        sa.Column("overall_rating", sa.Integer, nullable=False),
        *timestamps(),
    )
    op.create_primary_key(
        "pk_task_to_tasktaker_evalations", "task_to_tasktaker_evalations", ["todo_id", "tasktaker_id"]
    )
    op.execute(
        """
        CREATE TRIGGER update_task_to_taker_evalations_modtime
            BEFORE UPDATE
            ON task_to_tasktaker_evalations
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column()
        """
    )


def upgrade() -> None:
    create_updated_at_trigger()
    create_users_table()
    create_profle_table()
    # create_email_verification_table()
    create_todos_table()
    create_commment_table()
    create_note_table()
    create_task_offer_table()
    create_task_taker_evaluations_table()


def downgrade() -> None:
    op.drop_table("task_to_tasktaker_evalations")
    op.drop_table("user_task_for_todos")
    op.drop_table("comments")
    op.drop_table("notes")
    op.drop_table("todos")
    op.drop_table("profiles")
    # op.drop_table("email_verification")
    op.drop_table("users")
    op.execute("DROP FUNCTION update_updated_at_column")
