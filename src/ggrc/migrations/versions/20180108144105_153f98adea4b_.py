# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
empty message

Create Date: 2018-01-08 14:41:05.823885
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op


# revision identifiers, used by Alembic.
revision = '153f98adea4b'
down_revision = 'a60191406ca'


def upgrade():
  op.execute("""
       INSERT INTO access_control_roles
          (name, object_type, `read`, `update`,
           non_editable, internal, created_at, updated_at)
       VALUES ('ProposalReader', 'Proposal', 1, 0, 1, 1, NOW(), NOW()),
              ('ProposalEditor', 'Proposal', 0, 1, 1, 1, NOW(), NOW());
  """)


def downgrade():
  pass
