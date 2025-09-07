"""add_rtt_columns

Revision ID: 0eb0f581148e
Revises: ec476a4affe8
Create Date: 2025-09-07 21:56:45.019787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0eb0f581148e'
down_revision: Union[str, Sequence[str], None] = 'ec476a4affe8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
