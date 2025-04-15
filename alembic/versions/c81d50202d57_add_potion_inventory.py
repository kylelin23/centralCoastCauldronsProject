"""Add potion_inventory

Revision ID: c81d50202d57
Revises: adc339eb53f9
Create Date: 2025-04-14 17:31:12.420203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c81d50202d57'
down_revision: Union[str, None] = 'adc339eb53f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
