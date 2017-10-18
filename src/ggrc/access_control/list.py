# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Access Control List model"""

from ggrc import db
from ggrc.models import mixins
from ggrc.models import reflection


class AccessControlList(mixins.Base, db.Model):
  """Access Control List

  Model is a mapping between a role a person and an object. It gives the
  permission of the role to the person from that object.
  """
  __tablename__ = 'access_control_list'

  _api_attrs = reflection.ApiAttributes(
      "person",
      reflection.Attribute("person_id", create=False, update=False),
      "ac_role_id"
  )

  person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
  ac_role_id = db.Column(db.Integer, db.ForeignKey(
      'access_control_roles.id'), nullable=False)
  object_id = db.Column(db.Integer, nullable=False)
  object_type = db.Column(db.String, nullable=False)

  parent_id = db.Column(
      db.Integer,
      db.ForeignKey('access_control_list.id', ondelete='CASCADE'),
      nullable=True,
  )
  parent = db.relationship(
      lambda: AccessControlList,
      remote_side=lambda: AccessControlList.id
  )

  @property
  def object_attr(self):
    return '{0}_object'.format(self.object_type)

  @property
  def object(self):
    return getattr(self, self.object_attr)

  @object.setter
  def object(self, value):
    self.object_id = getattr(value, 'id', None)
    self.object_type = getattr(value, 'type', None)
    return setattr(self, self.object_attr, value)

  @staticmethod
  def _extra_table_args(_):
    return (
        db.UniqueConstraint(
            'person_id', 'ac_role_id', 'object_id', 'object_type'
        ),
        db.Index('idx_object_type_object_idx', 'object_type', 'object_id'),
    )
