# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
empty message

Create Date: 2018-01-04 16:22:17.763125
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a60191406ca'
down_revision = 'e9de00a0c8b'


def upgrade():
  op.execute("""
       update access_control_roles
       set notify_about_proposal = 1
       where object_type in ("Control", "Risk") and
             name in ("Admin", "Primary Contacts");
  """)


def downgrade():
  pass
