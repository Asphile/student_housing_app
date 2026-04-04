"""Update allocation and room_application column names

Revision ID: 4a1d6f8b7c3e
Revises: 39e5b2e7a1c2
Create Date: 2026-04-04 11:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4a1d6f8b7c3e'
down_revision = '39e5b2e7a1c2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('allocation', schema=None) as batch_op:
        batch_op.alter_column(
            'residence_id',
            new_column_name='listing_id',
            existing_type=sa.Integer(),
            nullable=False
        )
        batch_op.alter_column(
            'allocated_date',
            new_column_name='allocated_at',
            existing_type=sa.DateTime(),
            nullable=True
        )

    with op.batch_alter_table('room_application', schema=None) as batch_op:
        batch_op.alter_column(
            'date_submitted',
            new_column_name='applied_on',
            existing_type=sa.DateTime(),
            nullable=True
        )


def downgrade():
    with op.batch_alter_table('room_application', schema=None) as batch_op:
        batch_op.alter_column(
            'applied_on',
            new_column_name='date_submitted',
            existing_type=sa.DateTime(),
            nullable=True
        )

    with op.batch_alter_table('allocation', schema=None) as batch_op:
        batch_op.alter_column(
            'allocated_at',
            new_column_name='allocated_date',
            existing_type=sa.DateTime(),
            nullable=True
        )
        batch_op.alter_column(
            'listing_id',
            new_column_name='residence_id',
            existing_type=sa.Integer(),
            nullable=False
        )
