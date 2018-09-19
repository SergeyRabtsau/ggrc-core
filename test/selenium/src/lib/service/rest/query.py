# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants and methods for work with REST and QUERY API interactions."""
from lib.constants import value_aliases as alias


class Query(object):
  """Query API constants, templates, methods."""
  # pylint: disable=too-few-public-methods

  @staticmethod
  def expression_get_snapshoted_objs(
      obj_type, obj_ids, parent_type, parent_id):
    """Expression to get snapshoted object according to original and parent
    objects' attributes.
    """
    return {
        "expression": {
            "left": {
                "left": {
                    "left": "child_type",
                    "op": {"name": "="},
                    "right": obj_type
                },
                "op": {"name": "AND"},
                "right": {
                    "left": "child_id",
                    "op": {"name": "IN"},
                    "right": [str(obj_id) for obj_id in obj_ids]
                }
            },
            "op": {"name": "AND"},
            "right": {
                "object_name": parent_type,
                "op": {"name": "relevant"},
                "ids": [str(parent_id)]
            }
        }
    }

  @staticmethod
  def expression_get_obj_by_id(obj_id):
    """Expression to get object according to object's id.
    """
    return {
        "expression": {
            "left": "id",
            "op": {"name": alias.EQUAL_OP},
            "right": obj_id
        }
    }

  @staticmethod
  def expression_get_obj_by_code(obj_code):
    """Expression to get object according to object's code/slug.
    """
    return {
        "expression": {
            "left": "Code",
            "op": {"name": alias.EQUAL_OP},
            "right": obj_code
        }
    }

  @staticmethod
  def expression_get_comment_by_desc(parent_type, parent_id, comment_desc):
    """Expression to get comment object according to parent object's attributes
    and comment's description text w/o framing it (contains operation) to HTML
    tags cause of using Rich Text editor to form comment representation on UI.
    """
    return {
        "expression": {
            "left": {
                "object_name": parent_type,
                "op": {"name": "relevant"},
                "ids": [str(parent_id)]
            },
            "op": {"name": alias.AND_OP},
            "right": {
                "left": "description",
                "op": {"name": alias.CONTAINS_OP},
                "right": str(comment_desc)
            }
        }
    }

  @staticmethod
  def expression_get_person_by_email(email):
    """Expression to get person object by email"""
    return {
        "expression": {
            "left": "email",
            "op": {"name": "="},
            "right": email
        }
    }

  @staticmethod
  def expression_get_relevant_obj_to(relevant_obj_type, relevant_obj_id):
    """Expression to get object by relevant object id."""
    return  {
        "expression": {
            "object_name": relevant_obj_type,
            "op": {"name": "relevant"},
            "ids": [str(relevant_obj_id)]
        }
    }
