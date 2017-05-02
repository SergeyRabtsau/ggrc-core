# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
migrate urls to documents

Create Date: 2017-05-02 14:06:36.936410
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from datetime import datetime
from alembic import op
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import table, column, text


# revision identifiers, used by Alembic.
revision = '377d935e1b21'
down_revision = '178f7d2fb85e'

Base = automap_base()

HYPERLINKED_OBJECTS = {
    'Risk': 'risks',
    'Threat': 'threats'
}


def _get_relationships(connection, object_name, table_name):
  """Create documents and prepare relationships for insert."""
  urls_to_migrate = connection.execute(
      """
          SELECT id, url FROM {table_name}
          WHERE url > ''
          UNION
          SELECT id, reference_url FROM {table_name}
          WHERE reference_url > ''
      """.format(table_name=table_name)
  )

  Document = Base.classes.documents

  session = Session(connection)
  # workaround for issue fixed in Flask-SQLAlchemy v2.0
  # pylint: disable=W0212
  session._model_changes = {}

  now = datetime.now()
  relationships_to_add = []
  for object_id, url in urls_to_migrate:
    doc = Document(
        created_at=now,
        updated_at=now,
        title=url,
        link=url,
        document_type='REFERENCE_URL'
    )
    session.add(doc)
    session.commit()

    relationships_to_add.append({
        'source_id': object_id,
        'source_type': object_name,
        'destination_id': doc.id,
        'destination_type': 'Document',
        'created_at': now,
        'updated_at': now
    })
  session.close()
  return relationships_to_add


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()

  # reflect the tables
  Base.prepare(connection, reflect=True)

  relationships = table(
      'relationships',
      column('source_id', Integer),
      column('source_type', String),
      column('destination_id', Integer),
      column('destination_type', String),
      column('created_at', DateTime),
      column('updated_at', DateTime)
  )

  for object_name, table_name in HYPERLINKED_OBJECTS.iteritems():
    op.bulk_insert(relationships,
                   _get_relationships(connection, object_name, table_name))
    op.drop_column(table_name, 'url')
    op.drop_column(table_name, 'reference_url')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  connection = op.get_bind()

  update_url = """
      UPDATE {table_name}
      SET url=:url
      WHERE id = :object_id AND url IS NULL
  """

  update_reference_url = """
      UPDATE {table_name}
      SET reference_url=:url
      WHERE id = :object_id AND reference_url IS NULL AND url IS NOT NULL
  """

  delete_reletionships = """
       DELETE FROM relationships
       WHERE destination_type = 'Document'
         AND modified_by_id IS NULL
  """

  delete_document = """
      DELETE FROM documents
      WHERE id = {document_id}
  """

  for object_name, table_name in HYPERLINKED_OBJECTS.iteritems():
    op.add_column(table_name,
                  Column('url', String(length=250), nullable=True))
    op.add_column(table_name,
                  Column('reference_url', String(length=250), nullable=True))

    urls_to_migrate = connection.execute(
        """
            SELECT r.source_id, d.link, d.id  FROM documents d
            JOIN relationships r ON r.destination_id = d.id
            WHERE r.source_type = '{object_name}'
              AND r.destination_type = 'Document'
              AND r.modified_by_id IS NULL
              AND d.document_type = 'REFERENCE_URL'
            ORDER BY d.id
        """.format(object_name=object_name)
    )

    if not urls_to_migrate:
      continue

    for object_id, url, document_id in urls_to_migrate:
      connection.execute(
          text(update_reference_url.format(table_name=table_name)),
          object_id=object_id,
          url=url)
      connection.execute(
          text(update_url.format(table_name=table_name)),
          object_id=object_id,
          url=url)
      connection.execute(delete_document.format(document_id=document_id))

  connection.execute(delete_reletionships)
