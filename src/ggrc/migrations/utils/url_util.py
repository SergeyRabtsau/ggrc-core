# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Utils for migration of url and reference url values to documents table"""

from alembic import op
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Enum


def _create_documents(connection, object_type, table_name):
  """Create documents and prepare relationships for insert."""
  sql = """
        INSERT INTO temp_url (object_id, url, modified_by_id,
                              parent_created_at, parent_updated_at,
                              context_id, directive_type, system_type)
        SELECT id, url, modified_by_id, created_at, updated_at,
               context_id, {directive_type}, {system_type}
        FROM {table_name}
        WHERE url > ''
        UNION
        SELECT id, reference_url, modified_by_id, created_at, updated_at,
               context_id, {directive_type}, {system_type}
        FROM {table_name}
        WHERE reference_url > ''
    """

  directive_type, system_type = 'NULL', 'NULL'

  if table_name == 'directives':
    directive_type = 'meta_kind'
  elif table_name == 'systems':
    system_type = "IF(is_biz_process = 1, 'Process', 'System')"

  sql = sql.format(
      table_name=table_name,
      directive_type=directive_type,
      system_type=system_type
  )
  connection.execute(sql)

  connection.execute(
      """ INSERT INTO documents (modified_by_id, title, link, created_at,
                                 updated_at, document_type, context_id)
          SELECT modified_by_id, url, url, parent_created_at,
                 parent_updated_at, 'REFERENCE_URL', context_id
          FROM temp_url
          ORDER BY id
      """
  )

  # LAST_INSERT_ID() returns the value generated for the first inserted row
  # if you insert multiple rows using a single INSERT statement.
  # If no rows were successfully inserted, LAST_INSERT_ID() returns 0.
  last_id = int(connection.execute('SELECT LAST_INSERT_ID()').first()[0])

  if last_id:
    sql = """
          INSERT INTO relationships (modified_by_id,
                                     source_id,
                                     source_type,
                                     destination_id,
                                     destination_type,
                                     created_at,
                                     updated_at,
                                     context_id)
          SELECT t.modified_by_id,
                 t.object_id,
                 {object_type},
                 d.id,
                 'Document',
                 t.parent_created_at,
                 t.parent_updated_at,
                 d.context_id
          FROM temp_url t
          JOIN documents d ON d.id = t.id + {delta}
      """

    if table_name == 'directives':
      object_type = 't.directive_type'
    elif table_name == 'systems':
      object_type = 't.system_type'
    else:
      object_type = "'{}'".format(object_type)

    sql = sql.format(object_type=object_type, delta=last_id - 1)
    connection.execute(sql)

  connection.execute('TRUNCATE TABLE temp_url')


def migrate_urls_to_documents(objects):
  """Move url and reference url values to documents table"""
  op.alter_column(
      'documents', 'document_type',
      type_=Enum(u'URL', u'EVIDENCE', u'REFERENCE_URL'),
      existing_type=Enum(u'URL', u'EVIDENCE'),
      nullable=False,
      server_default=u'URL'
  )

  connection = op.get_bind()
  connection.execute("""
        CREATE TEMPORARY TABLE temp_url (
            id int(11) NOT NULL AUTO_INCREMENT,
            object_id int(11) NOT NULL,
            url varchar(250) NOT NULL,
            modified_by_id int(11) DEFAULT NULL,
            parent_created_at datetime NOT NULL,
            parent_updated_at datetime NOT NULL,
            context_id int(11) DEFAULT NULL,
            directive_type varchar(50) DEFAULT NULL,
            system_type varchar(50) DEFAULT NULL,
            PRIMARY KEY (id)
        )
    """)

  for object_type, table_name in objects.iteritems():
    _create_documents(connection, object_type, table_name)

  connection.execute('DROP TABLE temp_url')


def restore_url_columns(objects):
  """Restore url and reference_url columns for specified objects"""
  for table_name in objects.itervalues():
    op.add_column(table_name,
                  Column('url', String(length=250), nullable=True))
    op.add_column(table_name,
                  Column('reference_url', String(length=250), nullable=True))


def delete_reference_urls(object_types):
  """Delete reference URL documents and their relations to objects."""
  delete_reletionships = """
      DELETE FROM relationships
      WHERE (destination_type = 'Document'
         AND source_type IN ({object_types})
         AND destination_id IN (SELECT id FROM documents
                                WHERE document_type='REFERENCE_URL'))
         OR (destination_type IN ({object_types})
         AND source_type = 'Document'
         AND source_id IN (SELECT id FROM documents
                                WHERE document_type='REFERENCE_URL'))
   """

  delete_document = """
      DELETE FROM documents
      WHERE document_type='REFERENCE_URL'
   """

  object_types_to_delete = "'%s'" % "','".join(object_types)

  connection = op.get_bind()
  connection.execute(delete_document.format(
      object_types=object_types_to_delete))
  connection.execute(delete_reletionships.format(
      object_types=object_types_to_delete))

  op.alter_column(
      'documents', 'document_type',
      type_=Enum(u'URL', u'EVIDENCE'),
      existing_type=Enum(u'URL', u'EVIDENCE', u'REFERENCE_URL'),
      nullable=False,
      server_default=u'URL'
  )
