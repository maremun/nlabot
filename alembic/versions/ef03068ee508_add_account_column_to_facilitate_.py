"""Add account column to facilitate registration.

Revision ID: ef03068ee508
Revises: 8a1b3fad55e1
Create Date: 2017-11-03 11:02:02.447766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ef03068ee508'
down_revision = '8a1b3fad55e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('students', sa.Column('account', sa.String(length=128), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('students', 'account')
    # ### end Alembic commands ###
