# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""AccessControlList creation hooks."""

import datetime

from sqlalchemy import inspect

from ggrc.services import signals
from ggrc.models import all_models
from ggrc.models import comment
from ggrc import login
from ggrc.utils.revisions_diff import applier


def is_status_changed_to(required_status, obj):
  return (inspect(obj).attrs.status.history.has_changes() and
          obj.status == required_status)


def add_comment_to(obj, txt):
  if not isinstance(obj, comment.Commentable):
    return
  created_comment = all_models.Comment(
      description=txt,
      modified_by_id=login.get_current_user_id())
  all_models.Relationship(
      source=obj,
      destination=created_comment)


def build_text_comment(txt, proposal_link):
  return "{} \n\n link:{}".format(txt or "", proposal_link)


def apply_proposal(
    sender, obj=None, src=None, service=None,
    event=None, initial_state=None):  # noqa
  if not is_status_changed_to(obj.STATES.APPLIED, obj):
    return
  obj.applied_by = login.get_current_user()
  obj.apply_datetime = datetime.datetime.now()
  for field, value in obj.content.get("fields", {}).iteritems():
    if hasattr(obj.instance, field):
      setattr(obj.instance, field, value)
  applier.apply(obj.instance, obj.content)
  add_comment_to(obj.instance, obj.apply_reason or "")


def decline_proposal(
    sender, obj=None, src=None, service=None,
    event=None, initial_state=None):  # noqa
  if not is_status_changed_to(obj.STATES.DECLINED, obj):
    return
  obj.declined_by = login.get_current_user()
  obj.decline_datetime = datetime.datetime.now()
  add_comment_to(obj.instance, obj.decline_reason or "")


def make_proposal(
    sender, obj=None, src=None, service=None,
    event=None, initial_state=None):  # noqa
  obj.proposed_by = login.get_current_user()
  add_comment_to(obj.instance, obj.agenda or "")


def init_hook():
  signals.Restful.model_posted.connect(make_proposal,
                                       all_models.Proposal,
                                       weak=False)
  signals.Restful.model_put.connect(apply_proposal,
                                    all_models.Proposal,
                                    weak=False)
  signals.Restful.model_put.connect(decline_proposal,
                                    all_models.Proposal,
                                    weak=False)
