"""Criacao_tabelas_alertas_manual

Revision ID: 1905b3d9ffa6
Revises: 37add9bc4906
Create Date: 2025-09-01 17:53:34.947734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1905b3d9ffa6'
down_revision: Union[str, Sequence[str], None] = '37add9bc4906'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Dropar tabelas existentes se existem
    op.execute("DROP TABLE IF EXISTS alert_logs")
    op.execute("DROP TABLE IF EXISTS alerts")
    op.execute("DROP TABLE IF EXISTS alert_rules")
    
    # Criar tabela de alertas
    op.create_table('alerts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='active'),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('impact', sa.String(length=50), nullable=False, default='medium'),
        sa.Column('system', sa.String(length=255), nullable=False),
        sa.Column('assignee', sa.String(length=255), nullable=True),
        sa.Column('id_endpoint', sa.Integer(), nullable=True),
        sa.Column('id_user_created', sa.Integer(), nullable=False),
        sa.Column('id_user_assigned', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_endpoint'], ['endpoints.id']),
        sa.ForeignKeyConstraint(['id_user_created'], ['users.id']),
        sa.ForeignKeyConstraint(['id_user_assigned'], ['users.id'])
    )

    # Criar tabela de logs de alertas
    op.create_table('alert_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('id_alert', sa.Integer(), nullable=False),
        sa.Column('id_user', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['id_alert'], ['alerts.id']),
        sa.ForeignKeyConstraint(['id_user'], ['users.id'])
    )
    
    # Criar tabela de regras de alertas
    op.create_table('alert_rules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('condition', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('id_user_created', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['id_user_created'], ['users.id'])
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Dropar as tabelas na ordem correta (devido às foreign keys)
    op.drop_table('alert_logs')
    op.drop_table('alert_rules')
    op.drop_table('alerts')
