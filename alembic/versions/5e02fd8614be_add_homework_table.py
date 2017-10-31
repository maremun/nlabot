"""Add homework table.

Revision ID: 5e02fd8614be
Revises: 8a15a8263a21
Create Date: 2017-10-31 15:24:19.567471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e02fd8614be'
down_revision = '8a15a8263a21'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('homeworks',
                    sa.Column('hw_id', sa.Integer(), nullable=False),
                    sa.Column('total_pts', sa.Integer(), nullable=False),
                    sa.Column('n_func', sa.Integer(), nullable=False),
                    sa.Column('pts_per_func', sa.ARRAY(sa.Integer()),
                              nullable=False),
                    sa.PrimaryKeyConstraint('hw_id'))
    op.alter_column('submissions', 'hw_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    op.create_foreign_key(None, 'submissions', 'homeworks', ['hw_id'],
                          ['hw_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'submissions', type_='foreignkey')
    op.alter_column('submissions', 'hw_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.drop_table('homeworks')
    # ### end Alembic commands ###
