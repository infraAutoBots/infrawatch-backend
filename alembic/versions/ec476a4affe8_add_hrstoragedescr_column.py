"""add_hrstoragedescr_column

Revision ID: ec476a4affe8
Revises: b59f9b826609
Create Date: 2025-09-07 20:05:48.687614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec476a4affe8'
down_revision: Union[str, Sequence[str], None] = 'b59f9b826609'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adicionar coluna hrStorageDescr nas tabelas endpoints_data e endpoints_oids
    op.add_column('endpoints_data', sa.Column('hrStorageDescr', sa.String(), nullable=True))
    op.add_column('endpoints_oids', sa.Column('hrStorageDescr', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover coluna hrStorageDescr das tabelas
    op.drop_column('endpoints_oids', 'hrStorageDescr')
    op.drop_column('endpoints_data', 'hrStorageDescr')
