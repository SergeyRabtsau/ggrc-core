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
down_revision = '3aeaadf61cb4'

HYPERLINKED_OBJECTS = {
    'AccessGroup': 'access_groups',
    'Assessment': 'assessments',
    'Audit': 'audits',
    'Clause': 'clauses',
    'Control': 'controls',
    'DataAsset': 'data_assets',
    'Facility': 'facilities',
    'Issue': 'issues',
    'Market': 'markets',
    'Objective': 'objectives',
    'OrgGroup': 'org_groups',
    'Product': 'products',
    'Program': 'programs',
    'Project': 'projects',
    'Section': 'sections',
    'Vendor': 'vendors',

    # polymorphic types (tables containing multiple model types)
    'Directive': 'directives',
    'SystemOrProcess': 'systems',
}

# object types with all polymorphic types (i.e. object types sharing a common
# DB table with other obj types) "expanded"
HYPERLINKED_OBJ_TYPES = (
    set(HYPERLINKED_OBJECTS) -
    {'Directive', 'SystemOrProcess'} |
    {
        'Contract', 'Policy', 'Regulation', 'Standard',  # Directive types
        'System', 'Process'   # SystemOrProcess types
    }
)


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  url_util.migrate_urls_to_documents(HYPERLINKED_OBJECTS)


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  url_util.delete_reference_urls(HYPERLINKED_OBJ_TYPES)
