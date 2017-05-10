# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
migrate urls to documents

Create Date: 2017-05-02 14:01:00.127450
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from ggrc.migrations.utils import url_util


# revision identifiers, used by Alembic.
revision = '33f77e0b029c'
down_revision = '47d3cb39bad7'

HYPERLINKED_OBJECTS = {
    'AccessGroup': 'access_groups',
    'Assessment': 'assessments',
    'Audit': 'audits',
    'Clause': 'clauses',
    'Control': 'controls',
    'DataAsset': 'data_assets',
    'Directive': 'directives',
    'Facility': 'facilities',
    'Issue': 'issues',
    'Market': 'markets',
    'Objective': 'objectives',
    'OrgGroup': 'org_groups',
    'Product': 'products',
    'Program': 'programs',
    'Project': 'projects',
    'Section': 'sections',
    'System': 'systems',
    'Vendor': 'vendors'
}


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  url_util.migrate_urls_to_documents(HYPERLINKED_OBJECTS)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  url_util.restore_url_columns(HYPERLINKED_OBJECTS)
  url_util.migrate_urls_back(HYPERLINKED_OBJECTS)
