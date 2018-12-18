# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests builder of calendar events."""

from datetime import date
import urllib
from freezegun import freeze_time

from ggrc import db
from ggrc.models import all_models
from ggrc.gcalendar import calendar_event_builder
from integration.ggrc.models import factories
from integration.ggrc.gcalendar import BaseCalendarEventTest
from integration.ggrc_workflows.models import factories as wf_factories


# pylint: disable=protected-access
# pylint: disable=invalid-name
class TestCalendarEventBuilder(BaseCalendarEventTest):
  """Test calendar events builder class."""

  def setUp(self):
    """Set up test."""
    super(TestCalendarEventBuilder, self).setUp()
    self.client.get("/login")
    self.builder = calendar_event_builder.CalendarEventBuilder()

  def test_get_task_persons_ids_to_notify(self):
    """Test getting task persons ids that should be notified."""
    recipient_types = [u"Task Assignees", u"Task Secondary Assignees"]
    persons = [factories.PersonFactory(), factories.PersonFactory()]
    persons_ids = [person.id for person in persons]
    with factories.single_commit():
      obj = wf_factories.CycleTaskGroupObjectTaskFactory(
          end_date=date(2018, 1, 1),
      )
      for acl in obj._access_control_list:
        if acl.ac_role.name in recipient_types:
          for person in persons:
            factories.AccessControlPersonFactory(ac_list=acl, person=person)
    ids = calendar_event_builder.get_task_persons_ids_to_notify(obj)
    self.assertEqual(ids, set(persons_ids))

  def test_generate_description_for_event(self):
    """Test generating description for Calendar Event."""
    with factories.single_commit():
      person = factories.PersonFactory()
      event = factories.CalendarEventFactory(
          due_date=date(2015, 1, 10),
          attendee_id=person.id,
      )
      tasks = [
          wf_factories.CycleTaskGroupObjectTaskFactory(
              title=u"First task",
              end_date=date(2015, 1, 10),
          ),
          wf_factories.CycleTaskGroupObjectTaskFactory(
              title=u"Second task",
              end_date=date(2015, 1, 10),
          )
      ]
      for task in tasks:
        factories.RelationshipFactory(source=task, destination=event)
    self.builder._generate_description_for_event(event)
    link_not_encoded = (
        u'(("Task Status" IN ("Finished","Declined") and '
        u'"Needs Verification"=true) '
        u'or ("Task Status" IN ("Assigned","In Progress"))'
        u') and "Task Due Date"=01/10/2015'
    )
    expected_description = (
        u"You have due tasks for today.\n"
        u"- First task\n"
        u"- Second task\n"
        u"Please click on the link below to review and take action "
        u"on your task(s) due today.\n"
        u"<a href='http://localhost/dashboard#!task&query={link}'>Link</a>"
    ).format(link=urllib.quote(link_not_encoded.encode('utf-8')))
    self.assertEquals(event.description, expected_description)

  def test_create_event_with_relationship(self):
    """Test create event with a relationship."""
    with factories.single_commit():
      person = factories.PersonFactory()
      task = wf_factories.CycleTaskGroupObjectTaskFactory(
          title=u"First task",
          end_date=date(2015, 1, 15),
      )
    with freeze_time("2015-01-1 12:00:00"):
      event = self.builder._create_event_with_relationship(task, person.id)
      db.session.commit()

    self.assertEquals(event.title, u"Your tasks are due today")
    self.assertEquals(event.due_date.date(), date(2015, 1, 15))
    self.assertEquals(event.attendee_id, person.id)
    relationship = self.get_relationship(task.id, event.id)
    self.assertIsNotNone(relationship)

  def test_generate_events_for_task_without_event(self):
    """Test generating events for tasks without event."""
    with factories.single_commit():
      person = factories.PersonFactory()
      task = wf_factories.CycleTaskGroupObjectTaskFactory(
          end_date=date(2015, 1, 5),
      )
      for acl in task._access_control_list:
        factories.AccessControlPersonFactory(ac_list=acl, person=person)
    with freeze_time("2015-01-1 12:00:00"):
      self.builder._generate_events_for_task(task)
      db.session.commit()
    event = self.get_event(person.id, task.end_date)
    self.assertIsNotNone(event)
    relationship = self.get_relationship(task.id, event.id)
    self.assertIsNotNone(relationship)

  def test_generate_events_for_task_with_event_no_rel(self):
    """Test generating events for tasks with event but without relation."""
    with factories.single_commit():
      person = factories.PersonFactory()
      task = wf_factories.CycleTaskGroupObjectTaskFactory(
          end_date=date(2015, 1, 5),
      )
      factories.CalendarEventFactory(
          due_date=date(2015, 1, 5),
          attendee_id=person.id,
      )
      for acl in task._access_control_list:
        factories.AccessControlPersonFactory(ac_list=acl, person=person)
    with freeze_time("2015-01-1 12:00:00"):
      self.builder._generate_events_for_task(task)
      db.session.commit()
    event = self.get_event(person.id, task.end_date)
    self.assertIsNotNone(event)
    relationship = self.get_relationship(task.id, event.id)
    self.assertIsNotNone(relationship)

  def test_generate_events_for_task_with_event(self):
    """Test remove relationship to event for overdue task."""
    with factories.single_commit():
      person = factories.PersonFactory()
      task = wf_factories.CycleTaskGroupObjectTaskFactory(
          end_date=date(2015, 1, 1),
      )
      for acl in task._access_control_list:
        factories.AccessControlPersonFactory(ac_list=acl, person=person)
      event = factories.CalendarEventFactory(
          due_date=date(2015, 1, 1),
          attendee_id=person.id,
      )
      factories.RelationshipFactory(source=task, destination=event)
    with freeze_time("2015-01-5 12:00:00"):
      self.builder._generate_events_for_task(task)
      db.session.commit()
    event = self.get_event(person.id, task.end_date)
    self.assertIsNotNone(event)
    relationship = self.get_relationship(task.id, event.id)
    self.assertIsNone(relationship)

  def test_build_cycle_tasks(self):
    """Test generating one Calendar Event based on several cycle tasks."""
    with factories.single_commit():
      person = factories.PersonFactory()
      tasks = [
          wf_factories.CycleTaskGroupObjectTaskFactory(
              title=u"First task",
              end_date=date(2015, 1, 5),
          ),
          wf_factories.CycleTaskGroupObjectTaskFactory(
              title=u"Second task",
              end_date=date(2015, 1, 5),
          )
      ]
      for task in tasks:
        for acl in task._access_control_list:
          factories.AccessControlPersonFactory(ac_list=acl, person=person)

    with freeze_time("2015-01-01 12:00:00"):
      self.builder.build_cycle_tasks()
    self.assertEquals(all_models.CalendarEvent.query.count(), 1)
    event = self.get_event(person.id, task.end_date)
    self.assertIsNotNone(event)
    self.assertEquals(event.title, u"Your tasks are due today")
    link_not_encoded = (
        u'(("Task Status" IN ("Finished","Declined") and '
        u'"Needs Verification"=true) '
        u'or ("Task Status" IN ("Assigned","In Progress"))'
        u') and "Task Due Date"=01/05/2015'
    )
    expected_description = (
        u"You have due tasks for today.\n"
        u"- First task\n"
        u"- Second task\n"
        u"Please click on the link below to review and take action "
        u"on your task(s) due today.\n"
        u"<a href='http://localhost/dashboard#!task&query={link}'>Link</a>"
    ).format(link=urllib.quote(link_not_encoded.encode('utf-8')))
    self.assertEquals(event.description, expected_description)
    for task in tasks:
      relationship = self.get_relationship(task.id, event.id)
      self.assertIsNotNone(relationship)
