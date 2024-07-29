"""add status to order

Revision ID: 67fe3f279620
Revises: cb366fe51699
Create Date: 2024-07-18 17:57:04.858201

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67fe3f279620'
down_revision: Union[str, None] = 'cb366fe51699'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    order_status_enum = sa.Enum('Completed', 'Canceled', 'Ongoing','Delayed','Expired', name='order_status')
    order_status_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('order', sa.Column('order_status',order_status_enum ,nullable=False,server_default='Ongoing'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'order_status')
    order_status_enum = sa.Enum(name='order_status')
    order_status_enum.drop(op.get_bind(), checkfirst=True)
    # ### end Alembic commands ###
