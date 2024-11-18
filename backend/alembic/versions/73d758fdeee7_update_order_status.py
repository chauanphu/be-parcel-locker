"""Update order status

Revision ID: 73d758fdeee7
Revises: 6143ce629d89
Create Date: 2024-11-18 15:19:05.754117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '73d758fdeee7'
down_revision: Union[str, None] = '6143ce629d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

old_order_status = ('Completed', 'Canceled', 'Ongoing', 'Delayed', 'Expired', 'Packaging')
new_order_status = ('Packaging', 'Waiting', 'Ongoing', 'Delivered', 'Completed', 'Canceled', 'Delayed', 'Expired')

old_type = postgresql.ENUM(*old_order_status, name='order_status')
new_type = postgresql.ENUM(*new_order_status, name='order_status_new')

def upgrade() -> None:
    # Create new enum type if it doesn't exist
    with op.get_context().autocommit_block():
        op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'order_status_new') THEN
                CREATE TYPE order_status_new AS ENUM ('Packaging', 'Waiting', 'Ongoing', 'Delivered', 'Completed', 'Canceled', 'Delayed', 'Expired');
            END IF;
        END$$;
        """)
    
    # Update existing enum column to use new type
    with op.batch_alter_table('order') as batch_op:
        batch_op.alter_column('order_status',
                            type_=new_type,
                            postgresql_using="order_status::text::order_status_new")
    
    # Drop old enum type
    old_type.drop(op.get_bind(), checkfirst=False)
    
    # Rename new enum type to old name
    op.execute('ALTER TYPE order_status_new RENAME TO order_status')

def downgrade() -> None:
    # Create old enum type
    old_type.create(op.get_bind(), checkfirst=False)
    
    # Update existing enum column to use old type
    with op.batch_alter_table('order') as batch_op:
        batch_op.alter_column('order_status',
                            type_=old_type,
                            postgresql_using="order_status::text::order_status")
    
    # Drop new enum type
    new_type.drop(op.get_bind(), checkfirst=False)