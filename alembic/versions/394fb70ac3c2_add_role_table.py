"""Add role table

Revision ID: 394fb70ac3c2
Revises: ccb42477209e
Create Date: 2024-10-18 09:09:00.186315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '394fb70ac3c2'
down_revision: Union[str, None] = 'ccb42477209e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('permission',
    sa.Column('permission_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('permission_name', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('permission_id'),
    sa.UniqueConstraint('permission_name')
    )
    op.create_index(op.f('ix_permission_permission_id'), 'permission', ['permission_id'], unique=False)
    op.create_table('role_permission',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permission.permission_id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['role.role_id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('role_permission')
    op.drop_index(op.f('ix_permission_permission_id'), table_name='permission')
    op.drop_table('permission')
    # ### end Alembic commands ###