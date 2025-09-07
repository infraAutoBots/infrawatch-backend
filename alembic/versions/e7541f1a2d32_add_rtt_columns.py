"""add_rtt_columns

Revision ID: e7541f1a2d32
Revises: 0eb0f581148e
Create Date: 2025-09-07 21:56:53.495115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7541f1a2d32'
down_revision: Union[str, Sequence[str], None] = '0eb0f581148e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Adicionar colunas ping_rtt e snmp_rtt na tabela endpoints_data
    op.add_column('endpoints_data', sa.Column('ping_rtt', sa.String(), nullable=True))
    op.add_column('endpoints_data', sa.Column('snmp_rtt', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remover colunas ping_rtt e snmp_rtt
    op.drop_column('endpoints_data', 'snmp_rtt')
    op.drop_column('endpoints_data', 'ping_rtt')
