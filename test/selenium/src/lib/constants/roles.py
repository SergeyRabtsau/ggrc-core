# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Constants for roles."""

from lib.service.rest_service import AccessControlRolesService

# global roles
NO_ROLE = "No role"
NO_ROLE_UI = "(Inactive user)"
ADMIN = "Admin"
CREATOR = "Creator"
READER = "Reader"
EDITOR = "Editor"
ADMINISTRATOR = "Administrator"
# assessment roles
ASMT_CREATOR = CREATOR + "s"
ASSIGNEE = "Assignees"
VERIFIER = "Verifiers"
# program roles
PROGRAM_EDITOR = "Program Editor"
PROGRAM_MANAGER = "Program Manager"
PROGRAM_READER = "Program Reader"
# workflow roles
WORKFLOW_MEMBER = "Workflow Member"
WORKFLOW_MANAGER = "Workflow Manager"
# other roles
OBJECT_OWNERS = "Object Owners"
AUDIT_LEAD = "Audit Lead"
AUDITORS = "Auditors"
PRINCIPAL_ASSIGNEE = "Principal Assignee"
SECONDARY_ASSIGNEE = "Secondary Assignee"
PRIMARY_CONTACTS = "Primary Contacts"
SECONDARY_CONTACTS = "Secondary Contacts"

# user names
DEFAULT_USER = "Example User"

# user emails
DEFAULT_USER_EMAIL = "user@example.com"

# role scopes
SYSTEM = "System"
PRIVATE_PROGRAM = "Private Program"
WORKFLOW = "Workflow"
SUPERUSER = "Superuser"
NO_ACCESS = "No Access"

# Access control role ID
roles_dict = AccessControlRolesService().get_roles()
CONTROL_ADMIN_ID = roles_dict["Control"][ADMIN]
CONTROL_PRIMARY_CONTACT_ID = roles_dict["Control"][PRIMARY_CONTACTS]
ISSUE_ADMIN_ID = roles_dict["Issue"][ADMIN]
ISSUE_PRIMARY_CONTACT_ID = roles_dict["Issue"][PRIMARY_CONTACTS]
ASMT_CREATOR_ID = roles_dict["Assessment"][ASMT_CREATOR]
ASMT_ASSIGNEE_ID = roles_dict["Assessment"][ASSIGNEE]
ASMT_VERIFIER_ID = roles_dict["Assessment"][VERIFIER]
AUDIT_CAPTAIN_ID = roles_dict["Audit"]["Audit Captains"]
