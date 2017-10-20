# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""AccessControlList creation hooks."""
import sqlalchemy as sa
from collections import defaultdict
from sqlalchemy.orm.session import Session

from ggrc.access_control.role import get_custom_roles_for
from ggrc.models import all_models
from ggrc.models.hooks.relationship import create_related_roles
from ggrc.models.mixins.assignable import Assignable
from ggrc.models.relationship import Stub


def handle_acl_creation(session, flush_context):
  """Create relations for mapped objects."""
  base_objects = defaultdict(set)
  for obj in session.new:
    if isinstance(obj, all_models.AccessControlList):
      acr_id = obj.ac_role.id if obj.ac_role else obj.ac_role_id
      acr_name = get_custom_roles_for(obj.object_type).get(acr_id)
      if acr_name in Assignable.ASSIGNEE_TYPES:
        base_objects[Stub(obj.object_type, obj.object_id)].add(obj)

  if base_objects:
    create_related_roles(base_objects)


def init_hook():
  """Initialize AccessControlList-related hooks."""
  sa.event.listen(Session, "after_flush", handle_acl_creation)
