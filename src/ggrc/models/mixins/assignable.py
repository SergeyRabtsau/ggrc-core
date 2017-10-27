# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Contains the Assignable mixin.

This allows adding various assignee types to the object, like Verifiers,
Creators, etc.
"""

from collections import defaultdict

from ggrc.access_control.role import get_custom_roles_for


class Assignable(object):
  """Mixin for models with assignees"""

  ASSIGNEE_TYPES = ("Creators", "Assignees", "Verifiers")

  @property
  def assignees(self):
    """Property that returns assignees

    Returns:
        A set of assignees.
    """
    assignees = defaultdict(list)
    for acl in self.access_control_list:
      if acl.ac_role.name in self.assignee_roles:
        assignees[acl.person].append(acl.ac_role.name)

    return assignees

  @property
  def assignee_roles(self):
    """Property that returns assignee roles

    Returns:
        Dictionary with assignee role name and id
    """
    return {
        role_name: role_id
        for role_id, role_name in get_custom_roles_for(self.type).items()
        if role_name in self.ASSIGNEE_TYPES
    }
