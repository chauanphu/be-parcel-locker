"""Reset database to ground state

Revision ID: 3f924a4d7698
Revises: 1a3f2d0db80f
Create Date: 2024-11-14 09:01:34.968061

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import MetaData, text


# revision identifiers, used by Alembic.
revision: str = '3f924a4d7698'
down_revision: Union[str, None] = '1a3f2d0db80f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Get the active connection and reflect all tables
    conn = op.get_bind()
    meta = MetaData()
    meta.reflect(bind=conn)

    # Drop all tables in the current database
    for table in reversed(meta.sorted_tables):
        if table.name != "alembic_version":
            op.drop_table(table.name)
        
def downgrade() -> None:
    pass
