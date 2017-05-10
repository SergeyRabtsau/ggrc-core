# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
migrate urls to documents

Create Date: 2017-05-02 14:06:36.936410
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from ggrc.migrations.utils import url_util


# revision identifiers, used by Alembic.
revision = '377d935e1b21'
down_revision = '178f7d2fb85e'


HYPERLINKED_OBJECTS = {
    'Risk': 'risks',
    'Threat': 'threats'
}


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  url_util.migrate_urls_to_documents(HYPERLINKED_OBJECTS)


def downgrade():
  """Downgrade database schema and/or vdata back to the previous revision."""
  url_util.restore_url_columns(HYPERLINKED_OBJECTS)
  url_util.migrate_urls_back(HYPERLINKED_OBJECTS)
