"""add profile_id (fk user_id with profile) in recipient

Revision ID: 6c529dd0f1de
Revises: bbde89bb9c53
Create Date: 2024-09-05 23:07:56.615961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6c529dd0f1de'
down_revision: Union[str, None] = 'bbde89bb9c53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # op.add_column('profile', sa.Column('email', sa.String(), nullable=False))
    # op.add_column('profile', sa.Column('status', sa.Enum('Active', 'Inactive', 'Blocked', name='account_status'), nullable=False))
    # op.add_column('profile', sa.Column('Date_created', sa.DateTime(), nullable=False))
    
    # op.alter_column('profile', 'gender',
    #            existing_type=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_profile'),
    #            type_=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
    #            existing_nullable=True)
    
    # op.create_unique_constraint(None, 'profile', ['email'])
    
    
    
    # op.alter_column('recipient', 'gender',
    #            existing_type=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_recipient'),
    #            type_=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
               
    #            existing_nullable=True)
    check_column_query = sa.text(
        "SELECT EXISTS ("
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'recipient' AND column_name = 'profile_id')"
    )
    column_exists = op.get_bind().execute(check_column_query).scalar()

    # Add the column if it does not exist
    if not column_exists:
        op.add_column('recipient', sa.Column('profile_id', sa.Integer(), nullable=True))

    # Check if the index exists
    index_name = op.f('ix_recipient_profile_id')
    check_index_query = sa.text(
        "SELECT to_regclass(:index_name) IS NOT NULL"
    )
    index_exists = op.get_bind().execute(check_index_query, {"index_name": index_name}).scalar()

    # Create the index if it does not exist
    if not index_exists:
        op.create_index(index_name, 'recipient', ['profile_id'], unique=False)
        
        
    constraint_name = 'profile_id_of_recipient'
    check_constraint_query = sa.text(
        "SELECT CONSTRAINT_NAME FROM information_schema.table_constraints "
        "WHERE table_name = 'recipient' AND constraint_type = 'FOREIGN KEY' "
        "AND constraint_name = :constraint_name"
    )
    constraint_exists = op.get_bind().execute(check_constraint_query, {"constraint_name": constraint_name}).fetchone()

    # Create the foreign key constraint if it does not exist
    if not constraint_exists:
        op.create_foreign_key(
            constraint_name,
            'recipient',
            'profile',
            ['profile_id'],
            ['user_id']
        )
    
    
    op.alter_column('role', 'name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    
    # op.alter_column('shipper', 'gender',
    #            existing_type=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_shipper'),
    #            type_=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
    #            existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('shipper', 'gender',
    #            existing_type=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
    #            type_=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_shipper'),
    #            existing_nullable=True)
    op.alter_column('role', 'name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    
    op.drop_constraint('profile_id_of_recipient', 'recipient', type_='foreignkey')
    op.drop_index(op.f('ix_recipient_profile_id'), table_name='recipient')
    
    # op.alter_column('recipient', 'gender',
    #            existing_type=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
    #            type_=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_recipient'),
    #            existing_nullable=True)
    
    op.drop_column('recipient', 'profile_id')
    
    # op.drop_constraint(None, 'profile', type_='unique')
    # op.alter_column('profile', 'gender',
    #            existing_type=sa.Enum('Male', 'Female', 'Prefer not to respond', name='gender'),
    #            type_=postgresql.ENUM('Male', 'Female', 'Prefer not to respond', name='gender_profile'),
    #            existing_nullable=True)
    # op.drop_column('profile', 'Date_created')
    # op.drop_column('profile', 'status')
    # op.drop_column('profile', 'email')
    # ### end Alembic commands ###