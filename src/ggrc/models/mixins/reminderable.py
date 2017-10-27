# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Mixin for processing reminderable handlers"""


class Reminderable(object):
  """
  Mixin for processing various handlers for reminders
  """
  # pylint: disable=too-few-public-methods
  REMINDERABLE_HANDLERS = {}

  @staticmethod
  def handle_state_to_person_reminder(obj, data):
    """Handle reminder that are based on status of an object

    Args:
      obj: Model object that reminder is connected with
      data: handlers settings for deciding whether to process the notification
        at all and to who send the notification to. E.g. send it to verifiers
        if object In Progress.
      """
    # pylint: disable=protected-access
    from ggrc.notifications import notification_handlers
    from ggrc.models import notification

    if obj.status in data:
      assignee_type = data[obj.status]
      notif_name = "{}_{}_reminder".format(obj.type, assignee_type)
      notif_type = notification.NotificationType.query.filter_by(
          name=notif_name).first()
      notification_handlers._add_notification(obj, notif_type)
