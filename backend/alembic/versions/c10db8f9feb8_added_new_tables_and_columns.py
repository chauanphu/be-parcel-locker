"""Added new tables and columns

Revision ID: c10db8f9feb8
Revises: 91df3df2b02b
Create Date: 2024-08-09 21:54:55.177287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = 'c10db8f9feb8'
down_revision: Union[str, None] = '91df3df2b02b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
   
    
    status_enum = ENUM('Active', 'Inactive', 'Blocked', name='account_status', create_type=False)
    gender_recipient_enum = ENUM('Male', 'Female', 'Prefer not to respond', name='gender_recipient', create_type=False)
    gender_profile_enum = ENUM('Male', 'Female', 'Prefer not to respond', name='gender_profile', create_type=False)

    # Drop existing enum types if they exist
    op.execute("DROP TYPE IF EXISTS account_status CASCADE")
    op.execute("DROP TYPE IF EXISTS gender_recipient CASCADE")
    op.execute("DROP TYPE IF EXISTS gender_profile CASCADE")

    # Create new enum types
    status_enum.create(op.get_bind())
    gender_recipient_enum.create(op.get_bind())
    gender_profile_enum.create(op.get_bind())
    
    op.create_table('account',
    sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('username', sa.VARCHAR(length=20), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('status',status_enum , nullable=False),
    sa.Column('Date_created', sa.DateTime(), nullable=False),
    sa.Column('role', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_account_user_id'), 'account', ['user_id'], unique=False)
    op.create_table('recipient',
    sa.Column('recipient_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.Column('gender', gender_recipient_enum, nullable=False),
    sa.PrimaryKeyConstraint('recipient_id')
    )
    op.create_index(op.f('ix_recipient_recipient_id'), 'recipient', ['recipient_id'], unique=False)
    op.create_table('profile',
    sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('gender', gender_profile_enum, nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('address', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['account.user_id'], ),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_profile_user_id'), 'profile', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_profile_user_id'), table_name='profile')
    op.drop_table('profile')
    op.drop_index(op.f('ix_recipient_recipient_id'), table_name='recipient')
    op.drop_table('recipient')
    op.drop_index(op.f('ix_account_user_id'), table_name='account')
    op.drop_table('account')
    
    op.execute("DROP TYPE IF EXISTS account_status CASCADE")
    op.execute("DROP TYPE IF EXISTS gender_recipient CASCADE")
    op.execute("DROP TYPE IF EXISTS gender_profile CASCADE")

    
    # ### end Alembic commands ###