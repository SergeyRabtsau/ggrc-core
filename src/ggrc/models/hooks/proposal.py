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


def add_comment_about(proposal, reason, txt):
  if not isinstance(proposal.instance, comment.Commentable):
    return
  txt = txt or ""
  txt = txt.strip()
  if txt.startswith("<p>"):
    txt = txt[3:]
    if txt.endswith("</p>"):
      txt = txt[:-4]
  txt = txt.strip()
  comment_text = proposal.build_comment_text(reason, txt, proposal.proposed_by)
  created_comment = all_models.Comment(
      description=comment_text,
      modified_by_id=login.get_current_user_id(),
      reason_instance=proposal)
  all_models.Relationship(
      source=proposal.instance,
      destination=created_comment)


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
  add_comment_about(obj, obj.STATES.APPLIED, obj.apply_reason)


def decline_proposal(
    sender, obj=None, src=None, service=None,
    event=None, initial_state=None):  # noqa
  if not is_status_changed_to(obj.STATES.DECLINED, obj):
    return
  obj.declined_by = login.get_current_user()
  obj.decline_datetime = datetime.datetime.now()
  add_comment_about(obj, obj.STATES.DECLINED, obj.decline_reason)


def make_proposal(
    sender, obj=None, src=None, service=None,
    event=None, initial_state=None):  # noqa
  obj.proposed_by = login.get_current_user()
  add_comment_about(obj, obj.STATES.PROPOSED, obj.agenda)


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
