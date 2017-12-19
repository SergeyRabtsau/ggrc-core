# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
add proposal model

Create Date: 2017-12-01 14:48:45.907914
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

import sqlalchemy as sa

from sqlalchemy.dialects import mysql
from alembic import op

# revision identifiers, used by Alembic.
revision = '193b1a7e02d6'
down_revision = '3d505e157ab7'


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  op.create_table(
      'proposals',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('instance_id', sa.Integer(), nullable=False),
      sa.Column('instance_type', sa.String(length=250), nullable=False),
      sa.Column('content', mysql.LONGTEXT, nullable=False),
      sa.Column('agenda', sa.Text(), nullable=False),
      sa.Column('decline_reason', sa.Text(), nullable=False),
      sa.Column('decline_datetime', sa.DateTime(), nullable=True),
      sa.Column('declined_by_id', sa.Integer(), nullable=True),
      sa.Column('apply_reason', sa.Text(), nullable=False),
      sa.Column('apply_datetime', sa.DateTime(), nullable=True),
      sa.Column('applied_by_id', sa.Integer(), nullable=True),
      sa.Column('status', sa.String(length=250), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('modified_by_id', sa.Integer(), nullable=True),
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('context_id', sa.Integer(), nullable=True),
      sa.Column('proposed_by_id', sa.Integer(), nullable=True),
      sa.ForeignKeyConstraint(['applied_by_id'], ['people.id'], ),
      sa.ForeignKeyConstraint(['context_id'], ['contexts.id'], ),
      sa.ForeignKeyConstraint(['declined_by_id'], ['people.id'], ),
      sa.ForeignKeyConstraint(['proposed_by_id'], ['people.id'], ),
      sa.PrimaryKeyConstraint('id')
  )
  op.create_index('fk_instance',
                  'proposals',
                  ['instance_id', 'instance_type'],
                  unique=False)
  op.create_index('fk_proposal_contexts',
                  'proposals',
                  ['context_id'],
                  unique=False)
  op.create_index('ix_proposal_updated_at',
                  'proposals',
                  ['updated_at'],
                  unique=False)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  op.drop_index('ix_proposal_updated_at', table_name='proposals')
  op.drop_index('fk_proposal_contexts', table_name='proposals')
  op.drop_index('fk_instance', table_name='proposals')
  op.drop_table('proposals')
