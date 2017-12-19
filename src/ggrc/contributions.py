# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Lists of ggrc contributions."""

from ggrc.notifications import common
from ggrc.notifications import notification_handlers
from ggrc.notifications import data_handlers
from ggrc.utils import proposal


CONTRIBUTED_CRON_JOBS = [
    common.send_daily_digest_notifications,
]

HALF_HOUR_CRON_JOBS = [
    proposal.send_notification,
]

NOTIFICATION_LISTENERS = [
    notification_handlers.register_handlers
]


def contributed_notifications():
  """Get handler functions for ggrc notification file types."""
  return {
      "Assessment": data_handlers.get_assignable_data,
      "Comment": data_handlers.get_comment_data,
  }
