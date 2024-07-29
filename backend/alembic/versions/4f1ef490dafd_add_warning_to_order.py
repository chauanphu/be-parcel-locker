"""add warning to order

Revision ID: 4f1ef490dafd
Revises: 58d3d219d571
Create Date: 2024-07-29 22:16:41.050915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f1ef490dafd'
down_revision: Union[str, None] = '58d3d219d571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('warnings', sa.Boolean(), nullable=False))
    op.add_column('user', sa.Column('role', sa.Integer(), nullable=False,server_default='2'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'warnings')
    op.drop_column('user', 'role')
    # ### end Alembic commands ###
