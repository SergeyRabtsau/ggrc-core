# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>


"""Tests ordering for /query api."""

import ddt

import sqlalchemy as sa

from ggrc import db
from ggrc.models import AccessControlList
from ggrc.models import AccessControlRole
from ggrc.models import Assessment
from ggrc.models import Audit
from ggrc.models import Control
from ggrc.models import Person
from ggrc_workflows.models import TaskGroup

from integration.ggrc import TestCase
from integration.ggrc.query_helper import WithQueryApi


@ddt.ddt
class TestOrder(TestCase, WithQueryApi):
  """Tests people ordering"""

  @classmethod
  def setUpClass(cls):
    """Set up test cases for all tests."""
    TestCase.clear_data()
    # This imported file could be simplified a bit to speed up testing.
    cls.response = cls._import_file("people_order.csv")

  def setUp(self):
    self._check_csv_response(self.response, {})
    self.client.get("/login")

  def _check_ordering(self, object_name, sorted_titles, order_by):
    """Check query set ordering"""
    objects = self.simple_query(object_name,
                                order_by=[{"name": order_by, "desc": False}])
    titles = [obj['title'] for obj in objects]
    self.assertEqual(titles, sorted_titles)

    objects = self.simple_query(object_name,
                                order_by=[{"name": order_by, "desc": True}])
    titles = [obj['title'] for obj in objects]
    self.assertEqual(titles, list(reversed(sorted_titles)))

  def test_audit_captain(self):
    """Audit Captain ordering"""
    sorted_titles = [title for title, in db.session.query(Audit.title)
                     .filter(Person.id == Audit.contact_id)
                     .order_by(Person.email)]
    self._check_ordering("Audit", sorted_titles, "Audit Captain")

  @ddt.data("Assignees", "Creators", "Verifiers")
  def test_assessment_roles(self, role):
    """Assessment assignees/verifiers/creators ordering"""
    query = db.session.query(Assessment.title).join(
        AccessControlList,
        sa.and_(
            AccessControlList.object_type == "Assessment",
            AccessControlList.object_id == Assessment.id,
        )
    ).join(
        AccessControlRole,
        AccessControlRole.id == AccessControlList.ac_role_id
    ).join(
        Person, Person.id == AccessControlList.person_id
    ).filter(AccessControlRole.name == role).order_by(Person.email)

    sorted_titles = [a[0] for a in query]
    self._check_ordering("Assessment", sorted_titles, role)

  @ddt.data("Admin",
            "Primary Contacts",
            "Secondary Contacts",
            "Principal Assignees",
            "Secondary Assignees")
  def test_control_roles(self, role):
    """Control roles ordering"""
    sorted_titles = [title for title, in db.session.query(Control.title)
                     .filter(
                         AccessControlList.object_type == "Control",
                         AccessControlList.object_id == Control.id,
                         AccessControlList.ac_role_id == AccessControlRole.id,
                         AccessControlRole.name == role,
                         Person.id == AccessControlList.person_id)
                     .order_by(Person.email)]
    self._check_ordering("Control", sorted_titles, role)

  def test_task_group_assignee(self):
    """Task Group assignee ordering"""
    sorted_titles = [title for title, in db.session.query(TaskGroup.title)
                     .filter(Person.id == TaskGroup.contact_id)
                     .order_by(Person.email)]
    self._check_ordering("TaskGroup", sorted_titles, "Assignee")
