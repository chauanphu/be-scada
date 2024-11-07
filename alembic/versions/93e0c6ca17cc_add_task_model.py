"""add Task model

Revision ID: 93e0c6ca17cc
Revises: 761334764f60
Create Date: 2024-10-31 21:24:05.709801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '93e0c6ca17cc'
down_revision: Union[str, None] = '761334764f60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task_types',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('key', sa.String(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key'),
    sa.UniqueConstraint('value'),
    if_not_exists=True
    )
    status_enum = postgresql.ENUM(
        'PENDING', 'IN_PROGRESS', 'COMPLETED',
        name='taskstatus',
        create_type=True
    )
    with op.get_context().autocommit_block():
        status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('assignee_id', sa.Integer(), nullable=True),
    sa.Column('status', postgresql.ENUM(
        'PENDING', 'IN_PROGRESS', 'COMPLETED',
        name='taskstatus',
        create_type=False
    ), nullable=False),
    sa.ForeignKeyConstraint(['assignee_id'], ['account.user_id'], ),
    sa.ForeignKeyConstraint(['device_id'], ['units.id'], ),
    sa.ForeignKeyConstraint(['type_id'], ['task_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_audit_action'), 'audit', ['action'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_audit_action'), table_name='audit')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    status_enum = postgresql.ENUM(
        'PENDING', 'IN_PROGRESS', 'COMPLETED',
        name='taskstatus',
        create_type=True
    )
    with op.get_context().autocommit_block():
        status_enum.drop(op.get_bind(), checkfirst=False)
    
    op.drop_table('task_types')
    # ### end Alembic commands ###
