# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Defines a Revision model for storing snapshots."""

import sqlalchemy as sa

from ggrc import db
from ggrc.models import mixins
from ggrc.models import reflection
from ggrc.models import types
from ggrc.models import utils
from ggrc.fulltext import mixin as ft_mixin
from ggrc.utils import referenced_objects
from ggrc.rbac import permissions
from ggrc.utils.revisions_diff import builder
from ggrc import settings
from ggrc.models import comment


class JsonPolymorphicRelationship(utils.PolymorphicRelationship):

  def __call__(self, obj, json_obj):
    for field_name, prop_instance in obj.__class__.__dict__.iteritems():
      if prop_instance is self:
        instance = referenced_objects.get(json_obj[field_name]["type"],
                                          json_obj[field_name]["id"])
        assert isinstance(instance, Proposalable)
        return instance


class FullInstanceContentFased(utils.FasadeProperty):

  FIELD_NAME = "content"

  def prepare(self, src):
    src = super(FullInstanceContentFased, self).prepare(src)
    return builder.prepare(
        referenced_objects.get(src["instance"]["type"], src["instance"]["id"]),
        src["full_instance_content"])


class Proposal(mixins.person_relation_factory("applied_by"),
               mixins.person_relation_factory("declined_by"),
               mixins.person_relation_factory("proposed_by"),
               comment.CommentReasonable,
               mixins.Stateful,
               mixins.Base,
               ft_mixin.Indexed,
               db.Model):
  """Revision object holds a JSON snapshot of the object at a time."""

  __tablename__ = 'proposals'

  class NotificationContext(object):
    DIGEST_TITLE = "Proposal Digest"
    DIGEST_TMPL = settings.JINJA2.get_template(
        "notifications/proposal_digest.html")

  class STATES(object):
    PROPOSED = "proposed"
    APPLIED = "applied"
    DECLINED = "declined"

  class CommentTemplatesTextBuilder(object):
    PROPOSED_WITH_AGENDA = "Proposal has been created with comment: \n{text}"
    APPLIED_WITH_COMMENT = ("Proposal created by {user} has been applied "
                            "with a comment: \n{text}")
    DECLINED_WITH_COMMENT = ("Proposal created by {user} has been declined "
                            "with a comment: \n{text}")

    PROPOSED_WITHOUT_AGENDA = "Proposal has been created."
    APPLIED_WITHOUT_COMMENT = "Proposal created by {user} has been applied."
    DECLINED_WITHOUT_COMMENT = "Proposal created by {user} has been declined."


  def build_comment_text(self, reason, text, proposed_by):
    if reason == self.STATES.PROPOSED:
      with_tmpl = self.CommentTemplatesTextBuilder.PROPOSED_WITH_AGENDA
      without_tmpl = self.CommentTemplatesTextBuilder.PROPOSED_WITHOUT_AGENDA
    elif reason == self.STATES.APPLIED:
      with_tmpl = self.CommentTemplatesTextBuilder.APPLIED_WITH_COMMENT
      without_tmpl = self.CommentTemplatesTextBuilder.APPLIED_WITHOUT_COMMENT
    elif reason == self.STATES.DECLINED:
      with_tmpl = self.CommentTemplatesTextBuilder.DECLINED_WITH_COMMENT
      without_tmpl = self.CommentTemplatesTextBuilder.DECLINED_WITHOUT_COMMENT
    tmpl = with_tmpl if text else without_tmpl
    return tmpl.format(user=proposed_by.email, text=text)


  VALID_STATES = [STATES.PROPOSED, STATES.APPLIED, STATES.DECLINED]

  instance_id = db.Column(db.Integer, nullable=False)
  instance_type = db.Column(db.String, nullable=False)
  content = db.Column('content', types.LongJsonType, nullable=False)
  agenda = db.Column(db.Text, nullable=False, default=u"")
  decline_reason = db.Column(db.Text, nullable=False, default=u"")
  decline_datetime = db.Column(db.DateTime, nullable=True)
  apply_reason = db.Column(db.Text, nullable=False, default=u"")
  apply_datetime = db.Column(db.DateTime, nullable=True)
  proposed_notified_datetime = db.Column(db.DateTime, nullable=True)

  INSTANCE_TMPL = "{}_proposalable"

  instance = JsonPolymorphicRelationship("instance_id",
                                         "instance_type",
                                         INSTANCE_TMPL)

  _fulltext_attrs = [
      "instance_id",
      "instance_type",
      "agenda",
      "decline_reason",
      "decline_datetime",
      "apply_reason",
      "apply_datetime",
  ]

  _api_attrs = reflection.ApiAttributes(
      reflection.Attribute("instance", update=False),
      reflection.Attribute("content", create=False, update=False),
      reflection.Attribute("agenda", update=False),
      # ignore create proposal in specific state to be shure
      # new proposal will be only in proposed state
      reflection.Attribute('status', create=False),
      reflection.Attribute('decline_reason', create=False),
      reflection.Attribute('decline_datetime', create=False, update=False),
      reflection.Attribute('declined_by', create=False, update=False),
      reflection.Attribute('apply_reason', create=False),
      reflection.Attribute('apply_datetime', create=False, update=False),
      reflection.Attribute('applied_by', create=False, update=False),
      reflection.Attribute('full_instance_content',
                           create=True,
                           update=False,
                           read=False),
      reflection.Attribute('proposed_by', create=False, update=False),
  )

  full_instance_content = FullInstanceContentFased()

  @staticmethod
  def _extra_table_args(_):
    return (db.Index("fk_instance", "instance_id", "instance_type"), )


class Proposalable(object):

  @sa.ext.declarative.declared_attr
  def proposals(cls):  # pylint: disable=no-self-argument

    def join_function():
      return sa.and_(
          sa.orm.foreign(Proposal.instance_type) == cls.__name__,
          sa.orm.foreign(Proposal.instance_id) == cls.id,
      )

    return sa.orm.relationship(
        Proposal,
        primaryjoin=join_function,
        backref=Proposal.INSTANCE_TMPL.format(cls.__name__),
    )
