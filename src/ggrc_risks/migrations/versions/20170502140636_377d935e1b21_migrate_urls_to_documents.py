# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""
migrate urls to documents

Create Date: 2017-05-02 14:06:36.936410
"""
# disable Invalid constant name pylint warning for mandatory Alembic variables.
# pylint: disable=invalid-name

from alembic import op
from sqlalchemy import Column
from sqlalchemy import String


# revision identifiers, used by Alembic.
revision = '377d935e1b21'
down_revision = '178f7d2fb85e'


HYPERLINKED_OBJECTS = {
    'Risk': 'risks',
    'Threat': 'threats'
}


def _create_documents(connection, object_type, table_name):
  """Create documents and prepare relationships for insert."""

  connection.execute(
      """
          INSERT INTO temp_url (object_id, url, modified_by_id)
          SELECT id, url, modified_by_id
          FROM {table_name}
          WHERE url > ''
          UNION
          SELECT id, reference_url, modified_by_id
          FROM {table_name}
          WHERE reference_url > ''
      """.format(table_name=table_name)
  )

  connection.execute(
      """ INSERT INTO documents (modified_by_id, title, link, created_at, updated_at)
          SELECT modified_by_id, url, url, NOW(), NOW()
          FROM temp_url
          ORDER BY id
      """
  )

  last_id = int(connection.execute('SELECT LAST_INSERT_ID()').first()[0])

  if last_id:
    connection.execute(
        """
            INSERT INTO relationships (modified_by_id,
                                        source_id,
                                        source_type,
                                        destination_id,
                                        destination_type,
                                        created_at,
                                        updated_at)
            SELECT t.modified_by_id,
                  t.object_id,
                  '{object_type}',
                  d.id,
                  'Document',
                  NOW(),
                  NOW()
            FROM temp_url t
            JOIN documents d ON d.id = t.id + {delta}
        """.format(object_type=object_type, delta=last_id - 1)
    )

  connection.execute('TRUNCATE TABLE temp_url')


def upgrade():
  """Upgrade database schema and/or data, creating a new revision."""
  connection = op.get_bind()

  connection.execute("""
      CREATE TEMPORARY TABLE temp_url (
          id int(11) NOT NULL AUTO_INCREMENT,
          object_id int(11) NOT NULL,
          url varchar(250) NOT NULL,
          modified_by_id int(11) DEFAULT NULL,
          PRIMARY KEY (id)
      )
  """)

  for object_type, table_name in HYPERLINKED_OBJECTS.iteritems():
    _create_documents(connection, object_type, table_name)
    op.drop_column(table_name, 'url')
    op.drop_column(table_name, 'reference_url')

  connection.execute('DROP TABLE temp_url')


def _migrate_ulrs_back(connection, object_type, table_name):
  """Migrate url and reference_url back to an object table."""
  connection.execute(
      """
          INSERT INTO temp_relationship (object_id, document_id)
          SELECT source_id as object_id, destination_id as document_id
          FROM relationships
          WHERE source_type='{object_type}'
            AND destination_type='Document'
          UNION
          SELECT destination_id as object_id, source_id as document_id
          FROM relationships
          WHERE destination_type='{object_type}'
            AND source_type='Document'
      """.format(object_type=object_type))

  connection.execute(
      """
          INSERT INTO temp_url (object_id, document_id)
          SELECT object_id, MIN(document_id)
          FROM temp_relationship
          GROUP BY object_id
      """)

  connection.execute(
      """
          INSERT INTO temp_reference_url (object_id, document_id)
          SELECT object_id, MIN(document_id)
          FROM temp_relationship
          WHERE document_id NOT IN (SELECT document_id FROM temp_url)
          GROUP BY object_id
      """)

  connection.execute(
      """
          UPDATE {table_name} t
          JOIN temp_url u ON t.id = u.object_id
          JOIN documents d ON d.id = u.document_id
          SET t.url = d.link
      """.format(table_name=table_name))

  connection.execute(
      """
          UPDATE {table_name} t
          JOIN temp_reference_url u ON t.id = u.object_id
          JOIN documents d ON d.id = u.document_id
          SET t.reference_url = d.link
      """.format(table_name=table_name))

  connection.execute('TRUNCATE TABLE temp_relationship')
  connection.execute('TRUNCATE TABLE temp_url')
  connection.execute('TRUNCATE TABLE temp_reference_url')


def downgrade():
  """Downgrade database schema and/or data back to the previous revision."""
  connection = op.get_bind()

  connection.execute("""
      CREATE TEMPORARY TABLE temp_relationship (
          object_id int(11) NOT NULL,
          document_id int(11) NOT NULL
      )
  """)

  connection.execute("""
      CREATE TEMPORARY TABLE temp_url (
          object_id int(11) NOT NULL,
          document_id int(11) NOT NULL
      )
  """)

  connection.execute("""
      CREATE TEMPORARY TABLE temp_reference_url (
          object_id int(11) NOT NULL,
          document_id int(11) NOT NULL
      )
  """)

  for object_name, table_name in HYPERLINKED_OBJECTS.iteritems():
    op.add_column(table_name,
                  Column('url', String(length=250), nullable=True))
    op.add_column(table_name,
                  Column('reference_url', String(length=250), nullable=True))

    if object_name == 'Assessment':
      continue

    _migrate_ulrs_back(connection, object_name, table_name)

  delete_reletionships = """
      DELETE FROM relationships
      WHERE (destination_type = 'Document'
         AND source_type IN ({object_types}))
         OR (destination_type IN ({object_types})
         AND source_type = 'Document')
  """

  delete_document = """
      DELETE FROM documents
      WHERE id IN (SELECT destination_id
                   FROM relationships
                   WHERE destination_type = 'Document'
                     AND source_type IN ({object_types})
                   UNION
                   SELECT source_id
                   FROM relationships
                   WHERE destination_type IN ({object_types})
                     AND source_type = 'Document')
  """

  object_types_to_delete = ','.join(
      ["'%s'" % obj for obj in HYPERLINKED_OBJECTS.iterkeys()
       if obj != 'Assessment'])

  connection.execute(delete_document.format(
      object_types=object_types_to_delete))
  connection.execute(delete_reletionships.format(
      object_types=object_types_to_delete))

  connection.execute('DROP TABLE temp_relationship')
  connection.execute('DROP TABLE temp_url')
  connection.execute('DROP TABLE temp_reference_url')
