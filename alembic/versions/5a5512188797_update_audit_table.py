"""update audit table

Revision ID: 5a5512188797
Revises: 394fb70ac3c2
Create Date: 2024-10-18 20:33:09.252623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a5512188797'
down_revision: Union[str, None] = '394fb70ac3c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('audit', sa.Column('email', sa.String(length=255), nullable=False))
    op.drop_constraint('audit_user_id_fkey', 'audit', type_='foreignkey')
    op.drop_column('audit', 'user_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('audit', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_foreign_key('audit_user_id_fkey', 'audit', 'account', ['user_id'], ['user_id'])
    op.drop_column('audit', 'email')
    # ### end Alembic commands ###
