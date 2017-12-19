# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Proposal utils methods."""

import collections
import datetime
from werkzeug import exceptions
import urlparse

from ggrc.models import all_models
from ggrc.access_control import roleable

from google.appengine.api import mail
from ggrc import settings
from ggrc import db
from ggrc import rbac
from ggrc import utils


EmailProposalContext = collections.namedtuple(
    "EmailProposalContext",
    ["agenda",
     "proposed_by_name",
     "instance",
     "values_dict",
     "values_list_dict",
     "object_url"]
)


def _get_object_presentation(obj_dict):
  keys = ("display_name", "title", "name", "slug")
  return any(obj_dict.get(k) for k in keys) or "{}_{}".format(obj_dict["type"],
                                                              obj_dict["id"])


def get_fields_list_values(proposal, acr_dict, person_dict):

  list_fields = {}
  for acr_id, value in proposal.content["access_control_list"].iteritems():
    propose_dict = {}
    for action, items in value.iteritems():
      propose_dict[action] = [person_dict[int(i["id"])] for i in items]
    list_fields[acr_dict[int(acr_id)]] = propose_dict
  for field_name, value in proposal.content["mapping_list_fields"].iteritems():
    propose_dict = {}
    for action, items in value.iteritems():
      propose_dict[action] = [_get_object_presentation(i) for i in items]
    list_fields[field_name] = propose_dict
  return list_fields


def get_field_single_values(proposal, person_dict, cads_dict):
  values_dict = {}
  values_dict.update(proposal.content["fields"])
  proposed_cavs = proposal.content["custom_attribute_values"]
  for cad_id, value_obj in proposed_cavs.iteritems():
    if value_obj["attribute_object_id"]:
      if value_obj["attribute_value"] != "Person":
        # log it
        continue
      value = person_dict[int(value_obj["attribute_object_id"])]
    else:
      value = value_obj["attribute_value"]
    values_dict[cads_dict[cad_id]] = value

  values_dict.update({
      k: _get_object_presentation(v)
      for k, v in proposal.content["mapping_fields"].iteritems()
  })
  return values_dict


def get_object_url(obj):
  return urlparse.urljoin(utils.get_url_root(),
                          "{}/{}".format(obj._inflector.table_plural, obj.id))


def addressee_proposal_body_generator():
  notification_needed_proposal = all_models.Proposal.query.filter(
      all_models.Proposal.proposed_notified_datetime.is_(None),
      all_models.Proposal.apply_datetime.is_(None),
      all_models.Proposal.decline_datetime.is_(None),
  ).all()
  email_pools = collections.defaultdict(set)
  for proposal in notification_needed_proposal:
    if not isinstance(proposal.instance, roleable.Roleable):
      continue
    for acl in proposal.instance.access_control_list:
      if acl.person == proposal.proposed_by:
        # Don't need to send proposal digest to person who make proposal
        continue
      if acl.ac_role.notify_about_proposal:
        email_pools[acl.person].add(proposal)
  # cache wormup
  cads_dict = dict(all_models.CustomAttributeDefinition.query.values(
      all_models.CustomAttributeDefinition.id,
      all_models.CustomAttributeDefinition.title,
  ))
  person_dict = dict(all_models.Person.query.values(
      all_models.Person.id,
      all_models.Person.email,
  ))
  acr_dict = dict(all_models.AccessControlRole.query.values(
      all_models.AccessControlRole.id,
      all_models.AccessControlRole.name
  ))
  for addressee, proposals in email_pools.iteritems():
    body = all_models.Proposal.NotificationContext.DIGEST_TMPL.render(
        proposals=[
            EmailProposalContext(
                p.agenda,
                p.proposed_by.name or p.proposed_by.email,
                p.instance,
                get_field_single_values(p, person_dict, cads_dict),
                get_fields_list_values(p, acr_dict, person_dict),
                object_url=get_object_url(proposal.instance),
            )
            for p in proposals
        ]
    )
    yield (addressee, proposals, body)


def send_notification():
  now = datetime.datetime.now()
  for addressee, proposals, html in addressee_proposal_body_generator():
    mail.send_mail(
        sender=getattr(settings, 'APPENGINE_EMAIL'),
        to=addressee.email,
        subject=all_models.Proposal.NotificationContext.DIGEST_TITLE,
        body="",
        html=html,
    )
    for proposal in proposals:
      proposal.proposed_notified_datetime = now
  db.session.commit()


def present_notifications():
  if not rbac.permissions.is_admin():
    raise exceptions.Forbidden()
  generator = ("<h1> email to {}</h1>\n {}".format(addressee.email, body)
               for addressee, _, body in addressee_proposal_body_generator())
  return "".join(generator)
