# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
Add reasonable instance in Comment model

Create Date: 2018-01-03 15:10:48.355113
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'e9de00a0c8b'
down_revision = '1ade34010ee3'


def upgrade():
  op.add_column('comments', sa.Column('reason_instance_id', sa.Integer(), nullable=True))
  op.add_column('comments', sa.Column('reason_instance_type', sa.String(length=250), nullable=True))


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_column('comments', 'reason_instance_type')
  op.drop_column('comments', 'reason_instance_id')
