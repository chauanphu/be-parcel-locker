"""update the order_status

Revision ID: 09a9bb11bf91
Revises: e02c4d05648e
Create Date: 2024-09-30 14:49:26.921976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09a9bb11bf91'
down_revision: Union[str, None] = 'e02c4d05648e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    pass
    # ### end Alembic commands ###
