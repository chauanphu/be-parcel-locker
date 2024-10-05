"""test

Revision ID: e02c4d05648e
Revises: 6c529dd0f1de
Create Date: 2024-09-11 22:43:44.684969

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e02c4d05648e'
down_revision: Union[str, None] = '6c529dd0f1de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
