# Copyright (C) 2017 Google Inc.

# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Unittests for Revision model """

import unittest

import ddt
import mock

from ggrc.models import all_models


@ddt.ddt
class TestCheckPopulatedContent(unittest.TestCase):
  """Unittest checks populated content."""
  LIST_OF_REQUIRED_ROLES = [
      "Principal Assignees",
      "Secondary Assignees",
      "Primary Contacts",
      "Secondary Contacts",
  ]

  def setUp(self):
    super(TestCheckPopulatedContent, self).setUp()
    self.object_type = "Control"
    self.object_id = 1
    self.user_id = 123

  @ddt.data(
      # content, expected
      (None, None),
      ('principal_assessor', ("Principal Assignees", 1)),
      ('secondary_assessor', ("Secondary Assignees", 2)),
      ('contact', ("Primary Contacts", 3)),
      ('secondary_contact', ("Secondary Contacts", 4)),
      ('owners', ("Admin", 5)),
  )
  @ddt.unpack
  def test_check_populated_content(self, key, role):
    """Test populated content for revision if ACL doesn't exists."""
    content = {}
    if key:
      content[key] = {"id": self.user_id}
    expected = content.copy()
    expected["access_control_list"] = []
    role_dict = {}
    if role:
      role_name, role_id = role
      expected["access_control_list"].append({
          "display_name": role_name,
          "ac_role_id": role_id,
          "context_id": None,
          "created_at": None,
          "object_type": self.object_type,
          "updated_at": None,
          "object_id": self.object_id,
          "modified_by_id": None,
          "person_id": self.user_id,
          # Frontend require data in such format
          "person": {
              "id": self.user_id,
              "type": "Person",
              "href": "/api/people/{}".format(self.user_id)
          },
          "modified_by": None,
          "id": None,
      })
      role_dict[role_id] = role_name
    obj = mock.Mock()
    obj.id = self.object_id
    obj.__class__.__name__ = self.object_type
    revision = all_models.Revision(obj, mock.Mock(), mock.Mock(), content)

    with mock.patch("ggrc.access_control.role.get_custom_roles_for",
                    return_value=role_dict) as get_roles:
      self.assertEqual(revision.content, expected)
      get_roles.assert_called_once_with(self.object_type)

  @ddt.data(None, {}, {"id": None})
  def test_populated_content_no_user(self, user_dict):
    """Test populated content for revision without user id."""
    content = {"principal_assessor": user_dict}
    role_dict = {1: "Principal Assignees"}
    expected = content.copy()
    expected["access_control_list"] = []
    obj = mock.Mock()
    obj.id = self.object_id
    obj.__class__.__name__ = self.object_type
    revision = all_models.Revision(obj, mock.Mock(), mock.Mock(), content)
    with mock.patch("ggrc.access_control.role.get_custom_roles_for",
                    return_value=role_dict) as get_roles:
      self.assertEqual(revision.content, expected)
      get_roles.assert_called_once_with(self.object_type)

  @ddt.data(
      'principal_assessor',
      'secondary_assessor',
      'contact',
      'secondary_contact',
  )
  def test_populated_content_no_role(self, key):
    """Test populated content for revision without roles."""
    content = {key: {"id": self.user_id}}
    expected = content.copy()
    expected["access_control_list"] = []
    obj = mock.Mock()
    obj.id = self.object_id
    obj.__class__.__name__ = self.object_type
    revision = all_models.Revision(obj, mock.Mock(), mock.Mock(), content)
    with mock.patch("ggrc.access_control.role.get_custom_roles_for",
                    return_value={}) as get_roles:
      self.assertEqual(revision.content, expected)
      get_roles.assert_called_once_with(self.object_type)

  @ddt.data({'url': 'url1', 'reference_url': 'url2'})
  def test_populated_content_urls(self, content):
    """Test populated content for revision with urls."""
    expected = [{'display_name': 'url1',
                 'document_type': 'REFERENCE_URL',
                 'id': None,
                 'link': 'url1',
                 'title': 'url1'},
                {'display_name': 'url2',
                 'document_type': 'REFERENCE_URL',
                 'id': None,
                 'link': 'url2',
                 'title': 'url2'}]
    obj = mock.Mock()
    obj.id = self.object_id
    obj.__class__.__name__ = self.object_type
    revision = all_models.Revision(obj, mock.Mock(), mock.Mock(), content)
    with mock.patch("ggrc.access_control.role.get_custom_roles_for",
                    return_value={}):
      self.assertEqual(revision.content["reference_url"], expected)
