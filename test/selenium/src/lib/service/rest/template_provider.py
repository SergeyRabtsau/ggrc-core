# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Functionality for work with JSON templates."""

import json
import os

import inflection


class TemplateProvider(object):
  """Provider of methods for work with JSON templates."""

  @classmethod
  def generate_template_as_list(cls, json_tmpl_name, list_of_kwargs):
    """Get list of dictionaries to be sent to the app based on
    JSON file and passed `list_of_kwargs`
    Return list of dictionaries: [{type: {key: value, ...}}]
    """
    json_tmpl_name = inflection.underscore(json_tmpl_name)
    json_template = cls._get_json_template(json_tmpl_name)
    return [cls._json_for_obj(json_tmpl_name, json_template.copy(), kwargs)
            for kwargs in list_of_kwargs]

  @classmethod
  def _get_json_template(cls, json_tmpl_name):
    """Get JSON template"""
    path = os.path.join(
        os.path.dirname(__file__), "template/{0}.json".format(json_tmpl_name))
    with open(path) as json_file:
      json_data = json.load(json_file)
    return json_data

  @classmethod
  def _json_for_obj(cls, json_tmpl_name, json_template, kwargs):
    """Create a dictionary for obj based on JSON template and kwargs"""
    json_template.update({k: v for k, v in kwargs.iteritems() if v})
    return {json_tmpl_name: json_template}

  @staticmethod
  def update_template_as_dict(json_data_str, **kwargs):
    """Update JSON data string as dictionary according to
    attributes (items (kwargs): key=value).
    Return dictionary like as [{type: {key: value, ...}}].
    """
    json_data = json.loads(json_data_str)
    type = json_data.iterkeys().next()
    value = json_data.itervalues().next()
    value.update(kwargs)
    return {type: value}
