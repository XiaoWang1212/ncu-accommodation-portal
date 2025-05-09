"""delete user's firstName and lastName

Revision ID: f3a4392508a3
Revises: e3010c43d3c2
Create Date: 2025-05-09 00:51:45.318743

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a4392508a3'
down_revision = 'e3010c43d3c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.VARCHAR(length=50), nullable=True))

    # ### end Alembic commands ###
