"""v2 schema

Revision ID: d891077e0d1e
Revises: c81d50202d57
Create Date: 2025-04-16 23:26:52.044815

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd891077e0d1e'
down_revision: Union[str, None] = 'c81d50202d57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
