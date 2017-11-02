"""Change grade to grades array.

Revision ID: 8a1b3fad55e1
Revises: d58615acb9b8
Create Date: 2017-11-02 22:21:37.933038

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8a1b3fad55e1'
down_revision = 'd58615acb9b8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('students', sa.Column('grades', sa.ARRAY(sa.Float(precision=32)), nullable=False))
    op.drop_column('students', 'avg_grade')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('students', sa.Column('avg_grade', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.drop_column('students', 'grades')
    # ### end Alembic commands ###