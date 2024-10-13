"""add latitude/longitude

Revision ID: 01a1fefe15bc
Revises: 4a1c1309f2ab
Create Date: 2024-10-13 20:13:34.275333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01a1fefe15bc'
down_revision: Union[str, None] = '4a1c1309f2ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('status', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('status', sa.Column('longitude', sa.Float(), nullable=True))
    op.add_column('units', sa.Column('toggle', sa.Boolean(), nullable=True))
    op.add_column('units', sa.Column('on_time', sa.Time(), nullable=False))
    op.add_column('units', sa.Column('off_time', sa.Time(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('units', 'off_time')
    op.drop_column('units', 'on_time')
    op.drop_column('units', 'toggle')
    op.drop_column('status', 'longitude')
    op.drop_column('status', 'latitude')
    # ### end Alembic commands ###
