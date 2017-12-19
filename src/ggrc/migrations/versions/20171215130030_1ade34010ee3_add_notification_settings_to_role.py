# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
add notification settings to role

Create Date: 2017-12-15 13:00:30.997782
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '1ade34010ee3'
down_revision = '193b1a7e02d6'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.add_column('access_control_roles', sa.Column('notify_about_proposal',
                                                  sa.Boolean(),
                                                  nullable=False))
  op.add_column('proposals', sa.Column('proposed_notified_datetime',
                                       sa.DateTime(),
                                       nullable=True))


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_column('access_control_roles', 'notify_about_proposal')
  op.drop_column('proposals', 'proposed_notified_datetime')
