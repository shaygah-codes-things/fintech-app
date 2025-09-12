"""use CURRENT_TIMESTAMP defaults

Revision ID: 377a04f1b31b
Revises: df898220bd8c
Create Date: 2025-09-12 01:02:05.745342

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "377a04f1b31b"
down_revision: Union[str, None] = "df898220bd8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
