"""add state to conversations

Revision ID: 90ad8c0478a8
Revises: 
Create Date: 2025-12-14 17:09:35.536625
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "90ad8c0478a8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1️⃣ Create ENUM type explicitly
    conversation_state_enum = sa.Enum(
        "active",
        "archived",
        "deleted",
        name="conversationstate"
    )
    conversation_state_enum.create(op.get_bind(), checkfirst=True)

    # 2️⃣ Add column with default
    op.add_column(
        "conversations",
        sa.Column(
            "state",
            sa.Enum(
                "active",
                "archived",
                "deleted",
                name="conversationstate"
            ),
            nullable=False,
            server_default="active"
        )
    )


def downgrade() -> None:
    # 1️⃣ Drop column
    op.drop_column("conversations", "state")

    # 2️⃣ Drop ENUM type
    sa.Enum(
        "active",
        "archived",
        "deleted",
        name="conversationstate"
    ).drop(op.get_bind(), checkfirst=True)
