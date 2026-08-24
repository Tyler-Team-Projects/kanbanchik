"""merge heads: boards and workspaces

Revision ID: ddaa6a2a0c2f
Revises: 531612d42168, 58ccddf68352
Create Date: 2026-08-24 12:54:53.040713

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddaa6a2a0c2f'
down_revision: Union[str, Sequence[str], None] = ('531612d42168', '58ccddf68352')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
