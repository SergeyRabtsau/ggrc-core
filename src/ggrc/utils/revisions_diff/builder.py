# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Builder the prepare diff in special format between current
instance state and proposed content."""

import sqlalchemy as sa
import collections

from flask import g

from ggrc.models import reflection
from ggrc.models import mixins


def get_latest_revision_content(instance):
  from ggrc.models import all_models
  if not hasattr(g, "latest_revision_content"):
    g.latest_revision_content = {}
  key = (instance.type, instance.id)
  content = g.latest_revision_content.get(key)
  if not content:
    content = all_models.Revision.query.filter(
        all_models.Revision.resource_id == instance.id,
        all_models.Revision.resource_type == instance.type
    ).order_by(
        all_models.Revision.created_at.desc(),
        all_models.Revision.id.desc(),
    ).first().content
    g.latest_revision_content[key] = content
  return content


def get_person_email(person_id):
  if not hasattr(g, "person_email_cache"):
    from ggrc.models import all_models
    query = all_models.Person.query.values(all_models.Person.id,
                                           all_models.Person.email)
    g.person_email_cache = dict(query)
  return g.person_email_cache[person_id]


def person_obj_by_id(person_id):
  return {"id": person_id, "email": get_person_email(person_id)}


def generate_person_list(person_ids):
  person_ids = sorted([int(p) for p in person_ids])
  return [person_obj_by_id(i) for i in person_ids]


def generate_acl_diff(proposed, revisioned):
  proposed_acl = collections.defaultdict(set)
  revision_acl = collections.defaultdict(set)
  acl_ids = set()
  for acl in proposed:
    proposed_acl[acl["ac_role_id"]].add(acl["person"]["id"])
    acl_ids.add(acl["ac_role_id"])
  for acl in revisioned:
    revision_acl[acl["ac_role_id"]].add(acl["person"]["id"])
    acl_ids.add(acl["ac_role_id"])
  acl_dict = {}
  for role_id in acl_ids:
    deleted_person_ids = revision_acl[role_id] - proposed_acl[role_id]
    added_person_ids = proposed_acl[role_id] - revision_acl[role_id]
    if added_person_ids or deleted_person_ids:
      acl_dict[role_id] = {
          u"added": generate_person_list(added_person_ids),
          u"deleted": generate_person_list(deleted_person_ids),
      }
  return acl_dict


def populate_cavs(custom_attribute_values, custom_attributes, cads):
  # custom_attributes same as custom_attribute_values in revisions
  # custom_attributes empty on new api
  # in all that cases you shoul return custom_attribute_values
  if not custom_attributes or custom_attributes == custom_attribute_values:
    return custom_attribute_values
  custom_attributes = {int(k): v for k, v in custom_attributes.iteritems()}
  cavs = []
  for cad in cads:
    if cad.id not in custom_attributes:
      continue
    object_type = cad.attribute_type[4:].strip()
    if cad.attribute_type.startswith("Map:"):
      object_id = custom_attributes[cad.id].split(":", 1)[1].strip()
      object_id = None if object_id == 'None' else int(object_id)
      cavs.append({
          "attribute_value": object_type,
          "attribute_object_id": object_id,
          "custom_attribute_id": cad.id,
      })
    else:
      cavs.append({
          "attribute_value": custom_attributes[cad.id],
          "custom_attribute_id": cad.id,
          "attribute_object_id": None,
      })
  return cavs


def generate_cav_diff(instance, proposed, revisioned, old_style_cavs):
  if not isinstance(instance, mixins.customattributable.CustomAttributable):
    return {}
  proposed = populate_cavs(proposed,
                           old_style_cavs,
                           instance.custom_attribute_definitions)
  diff = {}
  remove_cav = bool(old_style_cavs is not None and proposed != old_style_cavs)
  proposed_cavs = {
      int(i["custom_attribute_id"]): (i["attribute_value"],
                                      i["attribute_object_id"])
      for i in proposed}
  revisioned_cavs = {
      int(i["custom_attribute_id"]): (i["attribute_value"],
                                      i["attribute_object_id"])
      for i in revisioned}
  for cad in instance.custom_attribute_definitions:
    if cad.id not in proposed_cavs:
      continue
    proposed_val = proposed_cavs[cad.id]
    cad_not_setuped = cad.id not in revisioned_cavs
    if cad_not_setuped or proposed_val != revisioned_cavs[cad.id]:
      value, person_id = proposed_val
      person = person_obj_by_id(person_id) if person_id else None
      diff[cad.id] = {
          "attribute_value": value,
          "attribute_object": person,
          "remove_cav": remove_cav,
      }
  return diff


def __mappting_key_function(object_dict):
  return object_dict["id"]


def _generate_list_mappings(keys, diff_data, current_data):
  result = {}
  for key in keys:
    if key not in diff_data:
      continue
    current = current_data.get(key) or []
    current_key_dict = {int(i["id"]): i for i in current}
    diff = diff_data.pop(key, None) or []
    diff_key_set = {int(i["id"]) for i in diff}
    current_diff_set = set(current_key_dict)
    deleted_ids = current_diff_set - diff_key_set
    added_ids = diff_key_set - current_diff_set
    if deleted_ids or added_ids:
      result[key] = {
          u"added": sorted(
              [i for i in diff if int(i["id"]) in added_ids],
              key=__mappting_key_function
          ),
          u"deleted": sorted(
              [i for i in current if int(i["id"]) in deleted_ids],
              key=__mappting_key_function
          ),
      }
  return result


def _generate_single_mappings(keys, diff_data, current_data):
  result = {}
  for key in keys:
    if key not in diff_data:
      continue
    current = current_data.get(key, None) or {"id": None, "type": None}
    diff = diff_data.pop(key, None) or {"id": None, "type": None}
    if current == diff:
      continue
    if diff["id"] is None:
      result[key] = None
    elif current["id"] is None or diff["id"] != current["id"]:
      result[key] = diff
  return result


def generate_mapping_dicts(instance, diff_data, current_data):

  relations = sa.inspection.inspect(instance.__class__).relationships
  relations_dict = collections.defaultdict(set)
  for rel in relations:
    relations_dict[rel.uselist].add(rel.key)
  descriptors = sa.inspection.inspect(instance.__class__).all_orm_descriptors
  for key, proxy in dict(descriptors).iteritems():
    if proxy.extension_type is sa.ext.associationproxy.ASSOCIATION_PROXY:
      relations_dict[True].add(key)
  return {
      "single_objects": _generate_single_mappings(relations_dict[False],
                                                  diff_data,
                                                  current_data),
      "list_objects": _generate_list_mappings(relations_dict[True],
                                              diff_data,
                                              current_data),
  }


def prepare(instance, content):
  api_attrs = reflection.AttributeInfo.gather_attr_dicts(instance.__class__,
                                                         "_api_attrs")
  updateable_fields = {k for k, v in api_attrs.iteritems() if v.update}
  current_data = get_latest_revision_content(instance)
  diff_data = {f: content[f]
               for f in updateable_fields
               if (f in current_data and
                   f in content and
                   current_data[f] != content[f])}
  acl = generate_acl_diff(diff_data.pop("access_control_list", []),
                          current_data.get("access_control_list", []))
  cav = generate_cav_diff(
      instance,
      diff_data.pop("custom_attribute_values", []),
      current_data.get("custom_attribute_values", []),
      diff_data.pop("custom_attributes", None),
  )
  generated_mapptings = generate_mapping_dicts(instance,
                                               diff_data,
                                               current_data)
  return {
      "fields": diff_data,
      "access_control_list": acl,
      "custom_attribute_values": cav,
      "mapping_fields": generated_mapptings["single_objects"],
      "mapping_list_fields": generated_mapptings["list_objects"],
  }
