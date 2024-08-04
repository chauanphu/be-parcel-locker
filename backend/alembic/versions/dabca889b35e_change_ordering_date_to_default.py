"""Change ordering date to default

Revision ID: dabca889b35e
Revises: d37e6e9e58d7
Create Date: 2024-08-04 11:38:01.858724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dabca889b35e'
down_revision: Union[str, None] = 'd37e6e9e58d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('order', 'ordering_date',
               existing_type=sa.DATE(),
               nullable=False,server_default=sa.text('NOW()'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('order', 'ordering_date',
               existing_type=sa.DATE(),
               nullable=True)
    # ### end Alembic commands ###
