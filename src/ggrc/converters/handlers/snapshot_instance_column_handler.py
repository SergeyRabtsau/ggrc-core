# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Handler for imports and exports snapshoted instances."""
import sqlalchemy
from sqlalchemy.orm import load_only

from cached_property import cached_property

from ggrc import db
from ggrc import models
from ggrc.converters import errors
from ggrc.converters.handlers.handlers import MappingColumnHandler
from ggrc.models.mixins.assignable import Assignable
from ggrc.snapshotter.rules import Types


class SnapshotInstanceColumnHandler(MappingColumnHandler):
  """Handler for mapping and unmapping instances over snapshot.

  Is used for Audit-scope objects; maps objects to Snapshots in the
  corresponding Audit scope.
  """

  @cached_property
  def related_audit(self):
    audit_column_handler = self.row_converter.objects.get("audit")
    if audit_column_handler:
      audit_items = audit_column_handler.parse_item()
      return audit_items[0]

  @cached_property
  def audit_object_pool_query(self):
    if self.row_converter.is_new and self.related_audit:
      return models.Snapshot.query.filter(
          models.Snapshot.parent_id == self.related_audit.id,
          models.Snapshot.parent_type == models.Audit.__name__,
          models.Snapshot.child_type == self.mapping_object.__name__,
      )
    else:
      sub = models.Relationship.get_related_query(
          self.row_converter.obj,
          models.Audit(),
      ).subquery("audit")
      case_statement = sqlalchemy.case(
          [
              (
                  sub.c.destination_type == models.Audit.__name__,
                  sub.c.destination_id,
              ),
          ],
          else_=sub.c.source_id,
      )
      return models.Snapshot.query.filter(
          models.Snapshot.parent_id == case_statement,
          models.Snapshot.parent_type == models.Audit.__name__,
          models.Snapshot.child_type == self.mapping_object.__name__,
      )

  @property
  def snapshoted_instances_query(self):
    """Property, return query of mapping objects

    It should be related to row instance over snapshot relation"""
    if self.row_converter.obj.id is None:
      # For new object query should be empty
      return self.mapping_object.query.filter(
          self.mapping_object.id.is_(None))
    rel_snapshots = models.Relationship.get_related_query(
        self.row_converter.obj, models.Snapshot(),
    ).subquery("snapshot_rel")
    case_statement = sqlalchemy.case(
        [
            (
                rel_snapshots.c.destination_type == models.Snapshot.__name__,
                rel_snapshots.c.destination_id,
            ),
        ],
        else_=rel_snapshots.c.source_id,
    )
    snapshot = models.Snapshot.query.filter(
        models.Snapshot.id == case_statement,
        models.Snapshot.child_type == self.mapping_object.__name__,
    ).options(
        load_only(models.Snapshot.child_id)
    ).subquery('snapshots')
    return self.mapping_object.query.filter(
        self.mapping_object.id == snapshot.c.child_id
    )

  def insert_object(self):
    "insert object handler"
    if self.dry_run or not self.value:
      return
    row_obj = self.row_converter.obj
    relationships = []
    child_id_snapshot_dict = {
        i.child_id: i for i in self.audit_object_pool_query.all()
    }
    for obj in self.value:
      snapshot = child_id_snapshot_dict.get(obj.id)
      mapping = models.Relationship.find_related(row_obj, snapshot)
      if not self.unmap and not mapping:
        mapping = models.Relationship(source=row_obj, destination=snapshot)
        relationships.append(mapping)
        db.session.add(mapping)
      elif self.unmap and mapping:
        db.session.delete(mapping)
    # Flush assignable ACL from session to have possibility to create
    # related ACLs with link to current one in parent_id
    acls = [
        obj for obj in db.session.new
        if isinstance(obj, models.AccessControlList) and
        obj.ac_role.name in Assignable.ASSIGNEE_TYPES
    ]
    db.session.flush(relationships + acls)
    self.dry_run = True

  def get_value(self):
    "return column value"
    if self.unmap or not self.mapping_object:
      return ""
    if self.row_converter.obj.type == models.Audit.__name__ and \
       self.mapping_object.__name__ in Types.all:
      # Audit should have the same mappings as Assessment. Mapped objects
      # will be loaded from snapshots.
      mapped_snapshots = self.row_converter.block_converter.mapped_snapshots
      snapshot_slugs = mapped_snapshots[self.row_converter.obj.id][
          self.mapping_object.__name__
      ]
      human_readable_ids = sorted(list(snapshot_slugs))
    else:
      objects = self.snapshoted_instances_query.all()
      human_readable_ids = [getattr(i, "slug", getattr(i, "email", None))
                            for i in objects]
    return "\n".join(human_readable_ids)

  def is_valid_creation(self, to_append_ids):
    "return True if data valid else False"
    if not to_append_ids:
      return True
    pool_ids = {i.child_id for i in self.audit_object_pool_query.all()}
    if to_append_ids - pool_ids:
      self.add_error(errors.ILLEGAL_APPEND_CONTROL_VALUE,
                     object_type=self.row_converter.obj.__class__.__name__,
                     mapped_type=self.mapping_object.__name__)
      return False
    return True

  def parse_item(self, *args, **kwargs):
    "parse items and make validation"
    items = super(SnapshotInstanceColumnHandler, self).parse_item(
        *args, **kwargs
    )
    if self.dry_run:
      # TODO: is_valid_creation should work with codes instead of ids and it
      # should also be checked on dry runs.
      return items
    exists_ids = {
        row.id for row in
        self.snapshoted_instances_query.values(self.mapping_object.id)
    }
    import_ids = {i.id for i in items or []}
    to_append_ids = import_ids - exists_ids
    self.is_valid_creation(to_append_ids)
    return items
