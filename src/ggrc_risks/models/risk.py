# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

from sqlalchemy.ext.declarative import declared_attr

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc.fulltext.mixin import Indexed
from ggrc.models.associationproxy import association_proxy
from ggrc.models import mixins
from ggrc.models.deferred import deferred
from ggrc.models.object_document import PublicDocumentable
from ggrc.models.object_person import Personable
from ggrc.models.reflection import PublishOnly
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState


class Risk(Roleable, HasObjectState, mixins.CustomAttributable, Relatable,
           Personable, PublicDocumentable,
           mixins.LastDeprecatedTimeboxed, mixins.BusinessObject,
           Indexed, db.Model):

  __tablename__ = 'risks'

  # Overriding mixin to make mandatory
  @declared_attr
  def description(cls):  # pylint: disable=no-self-argument
    return deferred(db.Column(db.Text, nullable=False), cls.__name__)

  risk_objects = db.relationship(
      'RiskObject', backref='risk', cascade='all, delete-orphan')
  objects = association_proxy('risk_objects', 'object', 'RiskObject')

  _publish_attrs = [
      'risk_objects',
      PublishOnly('objects'),
  ]

  _aliases = {
      "document_url": None,
      "document_evidence": None,
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are: \n {}".format('\n'.join(
              mixins.BusinessObject.VALID_STATES))
      }
  }
