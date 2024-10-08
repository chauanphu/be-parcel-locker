"""add date_created into all entity

Revision ID: 58d3d219d571
Revises: ff9d1f73f597
Create Date: 2024-07-29 15:56:31.382974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58d3d219d571'
down_revision: Union[str, None] = 'ff9d1f73f597'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    bind = op.get_bind()
    # Function to check if a column exists in a table
    def column_exists(table_name, column_name):
        query = f"""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND column_name = '{column_name}'
            );"""
        
        return bind.execute(sa.text(query)).scalar()
    
    
    # Add 'date_created' column to 'cell' table if it does not exist
    if not column_exists('cell', 'date_created'):
        op.add_column('cell', sa.Column('date_created', sa.DateTime(), nullable=False,server_default=sa.text('NOW()')))
        
    # Add 'date_created' column to 'locker' table if it does not exist    
    if not column_exists('locker', 'date_created'):
        op.add_column('locker', sa.Column('date_created', sa.DateTime(), nullable=False,server_default=sa.text('NOW()')))
        
    # Add 'date_created' column to 'parcel' table if it does not exist    
    if not column_exists('parcel', 'date_created'):
        op.add_column('parcel', sa.Column('date_created', sa.DateTime(), nullable=False,server_default=sa.text('NOW()')))

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('parcel', 'date_created')
    op.drop_column('locker', 'date_created')
    op.drop_column('cell', 'date_created')
    # ### end Alembic commands ###
