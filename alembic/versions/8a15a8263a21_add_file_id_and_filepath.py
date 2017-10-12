"""add file_id and filepath

Revision ID: 8a15a8263a21
Revises: f85137fd265a
Create Date: 2017-10-13 01:01:20.893924

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a15a8263a21'
down_revision = 'f85137fd265a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('submissions', sa.Column('file_id', sa.String(length=128), nullable=True))
    op.add_column('submissions', sa.Column('path', sa.String(length=256), nullable=True))
    op.create_unique_constraint(None, 'submissions', ['file_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('submissions', 'path')
    op.drop_column('submissions', 'file_id')
    # ### end Alembic commands ###
