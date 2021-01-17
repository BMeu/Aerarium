"""User Language

Revision ID: eb664d9fe242
Revises: b10a70fea24b
Create Date: 2018-11-26 20:37:53.644509

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb664d9fe242'
down_revision = 'b10a70fea24b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_settings', sa.Column('language', sa.String(length=5), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_settings', 'language')
    # ### end Alembic commands ###
