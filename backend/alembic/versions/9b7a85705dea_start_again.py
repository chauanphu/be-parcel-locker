"""start again

Revision ID: 9b7a85705dea
Revises: 3f924a4d7698
Create Date: 2024-11-14 09:20:42.437576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b7a85705dea'
down_revision: Union[str, None] = '3f924a4d7698'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Create ENUMs first
gender_enum = postgresql.ENUM(
    'Male', 'Female', 'PREFER_NOT_TO_RESPOND',
    name='genderenum',
    create_type=True
)
size_enum = postgresql.ENUM(
    'S', 'M', 'L',
    name='size',
    create_type=True
)
order_status_enum = postgresql.ENUM(
    'Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging',
    name='order_status',
    create_type=True
)

def upgrade() -> None:

    # Create ENUMs in a transaction
    with op.get_context().autocommit_block():
        gender_enum.create(op.get_bind(), checkfirst=True)
        size_enum.create(op.get_bind(), checkfirst=True)
        order_status_enum.create(op.get_bind(), checkfirst=True)

    # Create tables
    op.create_table('locker',
    sa.Column('locker_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.PrimaryKeyConstraint('locker_id')
    )
    op.create_index(op.f('ix_locker_locker_id'), 'locker', ['locker_id'], unique=False)
    op.create_table('parcel_type',
    sa.Column('parcel_type_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('parcel_type_id')
    )
    op.create_index(op.f('ix_parcel_type_parcel_type_id'), 'parcel_type', ['parcel_type_id'], unique=False)
    op.create_table('role',
    sa.Column('role_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('role_id')
    )
    op.create_index(op.f('ix_role_role_id'), 'role', ['role_id'], unique=False)
    op.create_table('account',
    sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=20), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('gender', postgresql.ENUM(
                'Male', 'Female', 'PREFER_NOT_TO_RESPOND',
                name='genderenum',
                create_type=False
            ), nullable=False),
    sa.Column('age', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('role', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role'], ['role.role_id'], ),
    sa.PrimaryKeyConstraint('user_id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone'),
    sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_account_user_id'), 'account', ['user_id'], unique=False)
    op.create_table('cell',
    sa.Column('locker_id', sa.Integer(), nullable=False),
    sa.Column('cell_id', sa.UUID(), nullable=False),
    sa.Column('size', postgresql.ENUM(
        'S', 'M', 'L',
        name='size',
        create_type=False
    ), nullable=False),
    sa.ForeignKeyConstraint(['locker_id'], ['locker.locker_id'], ),
    sa.PrimaryKeyConstraint('cell_id')
    )
    op.create_table('order',
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.Column('sending_cell_id', sa.UUID(), nullable=False),
    sa.Column('receiving_cell_id', sa.UUID(), nullable=False),
    sa.Column('ordering_date', sa.Date(), nullable=False),
    sa.Column('sending_date', sa.Date(), nullable=True),
    sa.Column('receiving_date', sa.Date(), nullable=True),
    sa.Column('order_status', postgresql.ENUM(
        'Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging',
        name='order_status',
        create_type=False
    ), nullable=False),
    sa.ForeignKeyConstraint(['receiving_cell_id'], ['cell.cell_id'], ),
    sa.ForeignKeyConstraint(['recipient_id'], ['account.user_id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['account.user_id'], ),
    sa.ForeignKeyConstraint(['sending_cell_id'], ['cell.cell_id'], ),
    sa.PrimaryKeyConstraint('order_id')
    )
    op.create_index(op.f('ix_order_order_id'), 'order', ['order_id'], unique=False)
    op.create_table('parcel',
    sa.Column('parcel_id', sa.Integer(), nullable=False),
    sa.Column('width', sa.Integer(), nullable=False),
    sa.Column('length', sa.Integer(), nullable=False),
    sa.Column('height', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Integer(), nullable=False),
    sa.Column('parcel_size', sa.String(), nullable=False),
    sa.Column('parcelType_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parcelType_id'], ['parcel_type.parcel_type_id'], ),
    sa.ForeignKeyConstraint(['parcel_id'], ['order.order_id'], ),
    sa.PrimaryKeyConstraint('parcel_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('parcel')
    op.drop_index(op.f('ix_order_order_id'), table_name='order')
    op.drop_table('order')
    op.drop_table('cell')
    op.drop_index(op.f('ix_account_user_id'), table_name='account')
    op.drop_table('account')
    op.drop_index(op.f('ix_role_role_id'), table_name='role')
    op.drop_table('role')
    op.drop_index(op.f('ix_parcel_type_parcel_type_id'), table_name='parcel_type')
    op.drop_table('parcel_type')
    op.drop_index(op.f('ix_locker_locker_id'), table_name='locker')
    op.drop_table('locker')

    # Drop ENUMs
    with op.get_context().autocommit_block():
        op.execute('DROP TYPE IF EXISTS genderenum')
        op.execute('DROP TYPE IF EXISTS size')
        op.execute('DROP TYPE IF EXISTS order_status')
    # ### end Alembic commands ###
