"""init

Revision ID: 76b0ff9e89ef
Revises: 
Create Date: 2024-03-26 09:16:35.298440

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76b0ff9e89ef'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    #Locker table
    locker_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='locker')"
    )).scalar()
    if not locker_exists:
        op.create_table('locker',
        sa.Column('locker_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('locker_id')
        )
    # Create index if not exists for locker
    locker_index_exists = op.get_bind().execute(sa.text(
        "SELECT to_regclass('ix_locker_locker_id') IS NOT NULL"
    )).scalar()
    if not locker_index_exists:
        op.create_index(op.f('ix_locker_locker_id'), 'locker', ['locker_id'], unique=False)
   
    #Parcel table
    parcel_type_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='parcel_type')"
    )).scalar()

    if not parcel_type_exists:
        op.create_table('parcel_type',
        sa.Column('parcel_type_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('parcel_type_id')
        )
    parcel_type_index_exists = op.get_bind().execute(sa.text(
        "SELECT to_regclass('ix_parcel_type_parcel_type_id') IS NOT NULL"
    )).scalar()
    if not parcel_type_index_exists:
        op.create_index(op.f('ix_parcel_type_parcel_type_id'), 'parcel_type', ['parcel_type_id'], unique=False)
    
    #User table
    user_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='user')"
    )).scalar()

    if not user_exists:
        op.create_table('user',
        sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('username', sa.VARCHAR(length=20), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('user_id', 'email')
        )
    user_index_exists = op.get_bind().execute(sa.text(
        "SELECT to_regclass('ix_user_user_id') IS NOT NULL"
    )).scalar()
    if not user_index_exists:
        op.create_index(op.f('ix_user_user_id'), 'user', ['user_id'], unique=False)
    
    #Cell table
    cell_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='cell')"
    )).scalar()

    if not cell_exists:
        op.create_table('cell',
        sa.Column('locker_id', sa.Integer(), nullable=False),
        sa.Column('cell_id', sa.UUID(), nullable=False),
        sa.Column('size', sa.Enum('S', 'M', 'L', name='size') , nullable=False),
        sa.Column('occupied', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['locker_id'], ['locker.locker_id'], ),
        sa.PrimaryKeyConstraint('cell_id')
        )
    
    #Order table
    order_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='order')"
    )).scalar()

    if not order_exists:
        op.create_table('order',
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('sending_cell_id', sa.UUID(), nullable=False),
        sa.Column('receiving_cell_id', sa.UUID(), nullable=False),
        sa.Column('ordering_date', sa.Date(), nullable=True),
        sa.Column('sending_date', sa.Date(), nullable=True),
        sa.Column('receiving_date', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['receiving_cell_id'], ['cell.cell_id'], ),
        sa.ForeignKeyConstraint(['sending_cell_id'], ['cell.cell_id'], ),
        sa.PrimaryKeyConstraint('order_id')
        )
    order_index_exists = op.get_bind().execute(sa.text(
        "SELECT to_regclass('ix_order_order_id') IS NOT NULL"
    )).scalar()
    if not order_index_exists:
        op.create_index(op.f('ix_order_order_id'), 'order', ['order_id'], unique=False)
    
    #Parcel table
    parcel_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='parcel')"
    )).scalar()

    if not parcel_exists:
        op.create_table('parcel',
        sa.Column('parcel_id', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('length', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Integer(), nullable=False),
        sa.Column('parcel_size', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['parcel_id'], ['order.order_id'], ),
        sa.PrimaryKeyConstraint('parcel_id')
        )

    #Role table
    role_exists = op.get_bind().execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='role')"
    )).scalar()

    if not role_exists:
        op.create_table('role',
        sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String()),
        sa.PrimaryKeyConstraint('role_id'),     
        )
    role_index_exists = op.get_bind().execute(sa.text(
        "SELECT to_regclass('ix_role_role_id') IS NOT NULL"
    )).scalar()
    if not role_index_exists:
        op.create_index(op.f('ix_role_role_id'), 'role', ['role_id'], unique=False)
    # ### end Alembic commands ###
    


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('parcel')
    op.drop_index(op.f('ix_order_order_id'), table_name='order')
    op.drop_table('order')
    op.drop_table('cell')
    
    # Drop all types named 'size'
    op.execute("DROP TYPE IF EXISTS size CASCADE")
            
    op.drop_index(op.f('ix_user_user_id'), table_name='user')
    op.drop_table('user')
    
    op.drop_index(op.f('ix_parcel_type_parcel_type_id'), table_name='parcel_type')
    op.drop_table('parcel_type')
    
    op.drop_index(op.f('ix_locker_locker_id'), table_name='locker')
    op.drop_table('locker')
    
    op.drop_index(op.f('ix_role_role_id'), table_name='role')
    op.drop_table('role')
    # ### end Alembic commands ###
