"""Rename student_id to id_number in user table

Revision ID: 39e5b2e7a1c2
Revises: 25bcd7a9f3f4
Create Date: 2026-04-04 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '39e5b2e7a1c2'
down_revision = '25bcd7a9f3f4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column(
            'student_id',
            new_column_name='id_number',
            existing_type=sa.String(length=13),
            nullable=True
        )


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column(
            'id_number',
            new_column_name='student_id',
            existing_type=sa.String(length=13),
            nullable=True
        )
