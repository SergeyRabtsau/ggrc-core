# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Util to get objects from flask.g.referenced_objects or DB if not present."""

import collections
import flask
from sqlalchemy import orm

from ggrc import db
from ggrc.models import inflector
from ggrc.models.mixins import customattributable


def get(type_, id_):
  """Check flask.g.referenced_objects for the object or get it from the DB."""
  if not id_:
    return None

  ref_objects = getattr(flask.g, "referenced_objects", {})

  if not (isinstance(type_, type) and issubclass(type_, db.Model)):
    type_ = inflector.get_model(type_)

  result = ref_objects.get(type_, {}).get(id_, None)

  if not result:
    result = type_.query.get(id_)

  return result


def mark_to_cache(type_, id_):
  """Mark object for warmup"""
  if not hasattr(flask.g, "referenced_objects_markers"):
    flask.g.referenced_objects_markers = collections.defaultdict(set)
  if not (isinstance(type_, type) and issubclass(type_, db.Model)):
    type_ = inflector.get_model(type_)
  flask.g.referenced_objects_markers[type_].add(id_)


def rewarm_cache():
  if not hasattr(flask.g, "referenced_objects_markers"):
    return
  if not hasattr(flask.g, "referenced_objects"):
    flask.g.referenced_objects = {}
  warm_cache = flask.g.referenced_objects_markers
  del flask.g.referenced_objects_markers
  for type_, ids in warm_cache.iteritems():
    if type_ not in flask.g.referenced_objects:
      flask.g.referenced_objects[type_] = {}
    query = type_.query.filter(type_.id.in_(ids))
    if issubclass(type_, customattributable.CustomAttributable):
      query = query.options(
          orm.Load(type_).subqueryload(
              "custom_attribute_definitions"
          ).undefer_group(
              "CustomAttributeDefinition_complete"
          )
      )
    for obj in query:
      flask.g.referenced_objects[type_][obj.id] = obj
    for id_ in ids:
      if id_ not in flask.g.referenced_objects[type_]:
        flask.g.referenced_objects[type_][id_] = None
