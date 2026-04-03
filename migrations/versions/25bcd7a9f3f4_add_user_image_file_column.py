"""Add image_file column to user table

Revision ID: 25bcd7a9f3f4
Revises: 07de44398fa6
Create Date: 2026-04-04 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '25bcd7a9f3f4'
down_revision = '07de44398fa6'
branch_labels = None
depends_on = None


def upgrade():
    # Add the missing image_file column to the user table.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image_file', sa.String(length=20), nullable=True))

    # Preserve existing profile pictures if the legacy column exists.
    op.execute('UPDATE "user" SET image_file = profile_picture WHERE profile_picture IS NOT NULL')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('image_file', existing_type=sa.String(length=20), nullable=False, server_default='default.jpg')


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('image_file')
