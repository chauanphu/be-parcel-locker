"""remove occupied col

Revision ID: 4c6869c10adf
Revises: 3208d8ac45f1
Create Date: 2024-11-08 18:58:43.530662

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4c6869c10adf'
down_revision: Union[str, None] = '3208d8ac45f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('cell', 'occupied')
    op.alter_column('order', 'order_status',
               existing_type=postgresql.ENUM('Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging', name='order_status'),
               type_=sa.Enum('Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging', name='order_status'),
               existing_nullable=False,
               existing_server_default=sa.text("'Packaging'::order_status"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('order', 'order_status',
               existing_type=sa.Enum('Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging', name='order_status'),
               type_=postgresql.ENUM('Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging', name='order_status'),
               existing_nullable=False,
               existing_server_default=sa.text("'Packaging'::order_status"))
    op.add_column('cell', sa.Column('occupied', sa.BOOLEAN(), autoincrement=False, nullable=False, default=False))
    # ### end Alembic commands ###
