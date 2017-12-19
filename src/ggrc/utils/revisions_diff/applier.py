# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Apply diff content to sent instance."""

from sqlalchemy import inspect

import collections
import itertools
from ggrc.access_control import roleable
from ggrc.models import all_models
from ggrc.models import mixins


def apply_acl_proposal(instance, content):
  if not isinstance(instance, roleable.Roleable):
    return
  instance_acl_dict = {(l.ac_role_id, l.person_id): l
                       for l in instance.access_control_list}
  person_ids = set()
  for role_id, data in content.get("access_control_list", {}).iteritems():
    person_ids |= {i["id"] for i in data["added"] + data["deleted"]}
  person_dict = {p.id: p for p in all_models.Person.query.filter(
      all_models.Person.id.in_(person_ids))
  }
  acr_dict = {
      i.id: i for i in all_models.AccessControlRole.query.filter(
          all_models.AccessControlRole.object_type == instance.type)
  }
  for role_id, data in content.get("access_control_list", {}).iteritems():
    role_id = int(role_id)
    for add in data["added"]:
      if (role_id, add["id"]) not in instance_acl_dict:
        # add ACL if it hasn't added yet
        all_models.AccessControlList(
            person=person_dict[add["id"]],
            ac_role=acr_dict[int(role_id)],
            object=instance,
        )
    for delete in data["deleted"]:
      if (role_id, delete["id"]) in instance_acl_dict:
        acl = instance_acl_dict[(role_id, delete["id"])]
        instance.access_control_list.remove(acl)


def apply_cav_proposal(instance, content):
  if not isinstance(instance, mixins.customattributable.CustomAttributable):
    return
  cad_dict = {d.id: d for d in instance.custom_attribute_definitions}
  cav_dict = {i.custom_attribute_id: i
              for i in instance.custom_attribute_values}
  proposals = content.get("custom_attribute_values", {})
  for cad_id, value in proposals.iteritems():
    cad = cad_dict.get(int(cad_id))
    if not cad:
      # looks like CAD was removed
      continue
    if value["attribute_object"]:
      attribute_object_id = value["attribute_object"]["id"]
      remove_cav = False
    else:
      attribute_object_id = None
      remove_cav = (cad.attribute_type.startswith("Map:") and
                    value.get("remove_cav"))
    cav = cav_dict.get(cad.id)
    if remove_cav and cav:
      instance.custom_attribute_values.remove(cav)
    elif not remove_cav and cav:
      cav.attribute_value = value["attribute_value"]
      cav.attribute_object_id = attribute_object_id
    elif not remove_cav:
      cav = all_models.CustomAttributeValue(
          custom_attribute=cad,
          attributable=instance,
          attribute_value=value["attribute_value"],
          attribute_object_id=attribute_object_id,
      )
      instance.custom_attribute_values.append(cav)


def apply_mapping(instance, content):
  relations = inspect(instance.__class__).relationships
  rel_names = [r.key for r in relations if not r.uselist]
  mapping_fields = content.get("mapping_fields", {})
  mapping_list_field = content.get("mapping_list_fields", {})
  all_models_dict = {m.__name__: m for m in all_models.all_models}
  all_items = itertools.chain(*[itertools.chain(v['added'], v['deleted'])
                                for v in mapping_list_field.values()])
  all_items = itertools.chain(mapping_fields.values(), all_items)
  update_field = collections.defaultdict(list)
  for value in all_items:
    if value:
      update_field[all_models_dict[value["type"]]].append(value["id"])
  field_cache = {(i.type, i.id): i
                 for m, ids in update_field.iteritems()
                 for i in m.query.filter(m.id.in_(ids))}
  for key, value in mapping_fields.iteritems():
    if key in rel_names:
      setattr(instance,
              key,
              field_cache.get((value["type"], value["id"])) if value else None)
  for key, value in mapping_list_field.iteritems():
    attr = getattr(instance, key)
    exist_items = {(i.type, i.id) for i in attr}
    for item in value["added"]:
      key = (item["type"], item["id"])
      if key in exist_items:
        continue
      attr.append(field_cache[key])
    for item in value["deleted"]:
      key = (item["type"], item["id"])
      if key not in exist_items:
        continue
      attr.remove(field_cache[key])


def apply(instance, content):
  apply_acl_proposal(instance, content)
  apply_cav_proposal(instance, content)
  apply_mapping(instance, content)
