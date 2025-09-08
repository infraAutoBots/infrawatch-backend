"""Create SLA tables manually

Revision ID: bfe1f8fb9ccc
Revises: 3b25c108d27d
Create Date: 2025-09-08 00:58:43.207204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfe1f8fb9ccc'
down_revision: Union[str, Sequence[str], None] = '3b25c108d27d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
