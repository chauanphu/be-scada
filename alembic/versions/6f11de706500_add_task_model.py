"""Add task model

Revision ID: 6f11de706500
Revises: 761334764f60
Create Date: 2024-10-31 15:31:23.280121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f11de706500'
down_revision: Union[str, None] = '761334764f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_audit_action'), 'audit', ['action'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_audit_action'), table_name='audit')
    # ### end Alembic commands ###
