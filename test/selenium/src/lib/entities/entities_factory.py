# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Factories that create entities."""
# pylint: disable=too-many-arguments
# pylint: disable=invalid-name
# pylint: disable=redefined-builtin

import copy
import random

from lib import factory, users
from lib.constants import (
    element, objects, roles, value_aliases, messages, object_states)
from lib.constants.element import AdminWidgetCustomAttributes
from lib.decorator import lazy_property
from lib.entities.entity import (
    PersonEntity, CustomAttributeDefinitionEntity, CommentEntity)
from lib.utils import help_utils, string_utils
from lib.utils.string_utils import StringMethods


class EntitiesFactory(object):
  """Common factory class for entities."""
  # pylint: disable=too-few-public-methods

  def __init__(self, obj_name):
    self.obj_name = obj_name
    self.obj_type = objects.get_obj_type(self.obj_name)
    self.obj_title = self.generate_string(self.obj_type)
    self.obj_entity_cls = factory.get_cls_obj_entity(object_name=self.obj_name)
    if self.__class__ not in [CustomAttributeDefinitionEntity, PersonEntity,
                              CommentEntity]:
      self.obj_slug = self.generate_slug()
    self._acl_roles = []

  def obj_inst(self):
    """Create object's instance and set value for attribute type."""
    return self.obj_entity_cls().update_attrs(
        is_allow_none=False, type=self.obj_type)

  def _create_random_obj(self, is_add_rest_attrs):
    """Create object's instance with random and predictable attributes' values.
    (method for overriding).
    """
    raise NotImplementedError

  def create(self, is_add_rest_attrs=False, **attrs):
    """Create random object's instance, if 'is_add_rest_attrs' then add
    attributes for REST, if 'attrs' then update attributes accordingly.
    """
    obj = self._create_random_obj(
        is_add_rest_attrs=is_add_rest_attrs).update_attrs(
        is_allow_none=False, **attrs)
    for acr_name, role_id, default_list in self._acl_roles:
      if acr_name in attrs:
        people_list = attrs[acr_name]
      else:
        people_list = default_list
      self._set_acl(obj, acr_name, people_list, role_id, is_add_rest_attrs)
    return obj

  @classmethod
  def generate_string(cls, first_part,
                      allowed_chars=StringMethods.ALLOWED_CHARS):
    """Generate random string in unicode format according to object type.
    Symbols allowed in random part may be specified by
    `allowed_chars` argument.
    """
    return unicode("{first_part}_{uuid}_{rand_str}".format(
        first_part=first_part, uuid=StringMethods.random_uuid(),
        rand_str=StringMethods.random_string(chars=allowed_chars)))

  @classmethod
  def generate_slug(cls):
    """Generate slug in unicode format according str part and random data."""
    return unicode("{slug}".format(slug=StringMethods.random_uuid()))

  @classmethod
  def generate_email(cls, domain=users.DEFAULT_EMAIL_DOMAIN):
    """Generate email in unicode format according to domain."""
    return unicode("{mail_name}@{domain}".format(
        mail_name=StringMethods.random_uuid(), domain=domain))

  def _set_acl(self, obj, acr_name, person_list, role_id, is_add_rest_attrs):
    """To be invoked in `create` method to set `access_control_list`
    and `acr_name` attributes.
    """
    if not hasattr(obj, "access_control_list"):
      obj.access_control_list = []
    attrs_to_set = {
        acr_name: PeopleFactory.extract_people_emails(person_list)
    }
    if is_add_rest_attrs:
      attrs_to_set["access_control_list"] = (
          obj.access_control_list +
          PeopleFactory.get_acl_members(role_id, person_list))
    obj.update_attrs(**attrs_to_set)


class PeopleFactory(EntitiesFactory):
  """Factory class for Persons entities."""

  def __init__(self):
    super(PeopleFactory, self).__init__(objects.PEOPLE)

  class __metaclass__(type):
    # pylint: disable=no-self-use

    @lazy_property
    def superuser(cls):
      """Return Person instance for default system superuser."""
      from lib.service import rest_service
      return rest_service.ObjectsInfoService().get_person(
          users.SUPERUSER_EMAIL)

  @staticmethod
  def extract_people_emails(people):
    """Extract values for person's email attributes."""
    return [
        person.email for person in help_utils.convert_to_list(people)
        if isinstance(person, PersonEntity)]

  @staticmethod
  def get_acl_members(role_id, people):
    """Return ACL the same members as list of dicts:
    [{ac_role_id: *, person: {id: *}, ...]
    """
    def get_acl_member(role_id, person):
      """Return ACL member as dict: {ac_role_id: *, person: {id: *}."""
      if isinstance(person, PersonEntity):
        return {"ac_role_id": role_id, "person": person.repr_min_dict()}
      else:
        raise ValueError(messages.CommonMessages.err_common.format(
            PersonEntity, person))
    return [get_acl_member(role_id, person)
            for person in help_utils.convert_to_list(people)]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Person entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    person_obj = self.obj_inst().update_attrs(
        name=self.obj_title, email=self.generate_email(),
        system_wide_role=unicode(random.choice(roles.GLOBAL_ROLES)))
    return person_obj


class UserRolesFactory(EntitiesFactory):
  """Factory class for user roles"""

  def __init__(self):
    super(UserRolesFactory, self).__init__(objects.USER_ROLES)

  def _create_random_obj(self, is_add_rest_attrs):
    """Create user role entity"""
    return self.obj_inst()


class CommentsFactory(EntitiesFactory):
  """Factory class for Comments entities."""

  def __init__(self):
    super(CommentsFactory, self).__init__(objects.COMMENTS)

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Comment entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    comment_obj = self.obj_inst().update_attrs(
        description=self.obj_title,
        modified_by=users.current_user().name)
    if is_add_rest_attrs:
      comment_obj.update_attrs(
          assignee_type=",".join((
              unicode(roles.PRIMARY_CONTACTS),
              unicode(roles.SECONDARY_CONTACTS))))
    return comment_obj


class CustomAttributeDefinitionsFactory(EntitiesFactory):
  """Factory class for entities."""

  def __init__(self):
    super(CustomAttributeDefinitionsFactory, self).__init__(
        objects.CUSTOM_ATTRIBUTES)

  @classmethod
  def generate_ca_values(cls, list_ca_def_objs, is_none_values=False):
    """Generate dictionary of CA random values from exist list CA definitions
    objects according to CA 'id', 'attribute_type' and 'multi_choice_options'
    for Dropdown. Return dictionary of CA items that ready to use via REST API:
    If 'is_none_values' then generate None like CA values according to CA
    definitions types.
    Example:
    list_ca_objs = [{'attribute_type': 'Text', 'id': 1},
    {'attribute_type': 'Dropdown', 'id': 2, 'multi_choice_options': 'a,b,c'}]
    :return {"1": "text_example", "2": "b"}
    """
    def generate_ca_value(cls, ca):
      """Generate CA value according to CA 'id', 'attribute_type' and
      'multi_choice_options' for Dropdown.
      """
      if not isinstance(ca, dict):
        ca = ca.__dict__
      ca_attr_type = ca.get("attribute_type")
      ca_value = None
      if ca_attr_type in AdminWidgetCustomAttributes.ALL_CA_TYPES:
        if not is_none_values:
          if ca_attr_type in (AdminWidgetCustomAttributes.TEXT,
                              AdminWidgetCustomAttributes.RICH_TEXT):
            ca_value = cls.generate_string(ca_attr_type)
          if ca_attr_type == AdminWidgetCustomAttributes.DATE:
            ca_value = unicode(ca["created_at"][:10])
          if ca_attr_type == AdminWidgetCustomAttributes.CHECKBOX:
            ca_value = random.choice((True, False))
          if ca_attr_type == AdminWidgetCustomAttributes.DROPDOWN:
            ca_value = unicode(
                random.choice(ca["multi_choice_options"].split(",")))
          if ca_attr_type == AdminWidgetCustomAttributes.PERSON:
            person_id = users.current_user().id
            ca_value = "Person:{}".format(person_id)
        else:
          ca_value = (
              None if ca_attr_type != AdminWidgetCustomAttributes.CHECKBOX
              else u"0")
      return {ca["id"]: ca_value}
    return {
        k: v for _ in [generate_ca_value(cls, ca) for ca in list_ca_def_objs]
        for k, v in _.items()}

  @staticmethod
  def generate_ca_defenitions_for_asmt_tmpls(list_ca_definitions):
    """Generate list of dictionaries of CA random values from exist list CA
    definitions according to CA 'title', 'attribute_type',
    'multi_choice_options' and 'multi_choice_mandatory' for Dropdown.
    Return list of dictionaries of CA definitions that ready to use
    via REST API:
    Example:
    :return
    [{"title": "t1", "attribute_type": "Text", "multi_choice_options": "",
      "multi_choice_mandatory": ""},
     {"title":"t2", "attribute_type":"Rich Text", "multi_choice_options":"",
      "multi_choice_mandatory": ""}]
    """
    return [{k: (v if v else "") for k, v in ca_def.__dict__.items()
             if k in ("title", "attribute_type", "multi_choice_options",
                      "multi_choice_mandatory")}
            for ca_def in list_ca_definitions]

  def create_dashboard_ca(self, definition_type):
    """Create and return CA entity with valid filled fields for creating
    N'Dashboard'.
    """
    return self.obj_inst().update_attrs(
        title=self.generate_ca_title(value_aliases.DASHBOARD),
        attribute_type=AdminWidgetCustomAttributes.TEXT,
        definition_type=definition_type, mandatory=False)

  def create(self, is_add_rest_attrs=False, **attrs):
    """Create random Custom Attribute object's instance, if
    'is_add_rest_attrs' then add attributes for REST, if 'attrs' then update
    attributes accordingly.
    """
    obj = self.obj_inst()
    independent_default_values = {
      "attribute_type": random.choice(
          AdminWidgetCustomAttributes.ALL_CA_TYPES),
      "definition_type": objects.get_singular(
          random.choice(objects.ALL_CA_OBJS)),
      "mandatory": False,
      "placeholder": None
    }
    for name, default_value in independent_default_values.iteritems():
      value = attrs.get(name, default_value)
      setattr(obj, name, value)
    obj.title = attrs.get("title", self.generate_ca_title(obj.attribute_type))
    if obj.attribute_type == AdminWidgetCustomAttributes.DROPDOWN:
      obj.multi_choice_options = attrs.get(
          "multi_choice_options", StringMethods.random_list_strings())
    else:
      obj.multi_choice_options = None
    if is_add_rest_attrs:
      obj.modal_title = "Add Attribute to type {}".format(
          obj.definition_type.title())
    return obj

  def generate_ca_title(self, first_part):
    """Generate title of custom attribute
    (same as usual title but without a star as it's disallowed, see GGRC-4954)
    """
    chars = StringMethods.ALLOWED_CHARS.replace(string_utils.Symbols.STAR,
                                                string_utils.Symbols.BLANK)
    return self.generate_string(first_part, allowed_chars=chars)


class ProgramsFactory(EntitiesFactory):
  """Factory class for Programs entities."""

  def __init__(self):
    super(ProgramsFactory, self).__init__(objects.PROGRAMS)
    self._acl_roles = [
        ("managers", roles.ACLRolesIDs.PROGRAM_MANAGERS,
         [users.current_user()])
    ]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Program entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    program_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        status=unicode(object_states.DRAFT),
        os_state=unicode(element.ReviewStates.UNREVIEWED))
    if is_add_rest_attrs:
      program_obj.update_attrs(
          recipients=",".join((
              unicode(roles.ADMIN), unicode(roles.PRIMARY_CONTACTS),
              unicode(roles.SECONDARY_CONTACTS))))
    return program_obj


class ControlsFactory(EntitiesFactory):
  """Factory class for Controls entities."""
  def __init__(self):
    super(ControlsFactory, self).__init__(objects.CONTROLS)
    self._acl_roles = [
        ("admins", roles.ACLRolesIDs.CONTROL_ADMINS, [users.current_user()])
    ]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Control entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    control_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        status=unicode(object_states.DRAFT),
        os_state=unicode(element.ReviewStates.UNREVIEWED))
    if is_add_rest_attrs:
      control_obj.update_attrs(
          recipients=",".join((
              unicode(roles.ADMIN), unicode(roles.PRIMARY_CONTACTS),
              unicode(roles.SECONDARY_CONTACTS))))
    return control_obj


class ObjectivesFactory(EntitiesFactory):
  """Factory class for Objectives entities."""
  def __init__(self):
    super(ObjectivesFactory, self).__init__(objects.OBJECTIVES)
    self._acl_roles = [
        ("admins", roles.ACLRolesIDs.OBJECTIVE_ADMINS, [users.current_user()])
    ]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Objective entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    objective_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        status=unicode(object_states.DRAFT),
        os_state=unicode(element.ReviewStates.UNREVIEWED))
    if is_add_rest_attrs:
      objective_obj.update_attrs(
          recipients=",".join((
              unicode(roles.ADMIN), unicode(roles.PRIMARY_CONTACTS),
              unicode(roles.SECONDARY_CONTACTS))))
    return objective_obj


class AuditsFactory(EntitiesFactory):
  """Factory class for Audit entity."""
  def __init__(self):
    super(AuditsFactory, self).__init__(objects.AUDITS)
    self._acl_roles = [
        ("audit_captains", roles.ACLRolesIDs.AUDIT_CAPTAINS,
         [users.current_user()]),
        ("auditors", roles.ACLRolesIDs.AUDITORS, [])
    ]

  @staticmethod
  def clone(audit, count_to_clone=1):
    """Clone Audit entity (count depends on 'count_to_clone')
    and set attributes' values related to parallelization to None, title will
    be predicted.
    """
    # pylint: disable=anomalous-backslash-in-string
    return [copy.deepcopy(audit).update_attrs(
        title=unicode(audit.title + " - copy " + str(num)), slug=None,
        created_at=None, updated_at=None, href=None, url=None, id=None)
        for num in xrange(1, count_to_clone + 1)]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Audit entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    audit_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        os_state=unicode(object_states.PLANNED))
    return audit_obj


class AssessmentTemplatesFactory(EntitiesFactory):
  """Factory class for Assessment Templates entities."""

  def __init__(self):
    super(AssessmentTemplatesFactory, self).__init__(
        objects.ASSESSMENT_TEMPLATES)

  @staticmethod
  def clone(asmt_tmpl, count_to_clone=1):
    """Clone Assessment Template entity (count depends on 'count_to_clone')
    and set attributes' values related to parallelization to None.
    """
    return [copy.deepcopy(asmt_tmpl).update_attrs(
        slug=None, updated_at=None, href=None, url=None, id=None)
        for _ in xrange(1, count_to_clone + 1)]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Assessment Template entity with randomly and predictably filled
    fields, if 'is_add_rest_attrs' then add attributes for REST."""
    asmt_tmpl_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        assignees=unicode(roles.PRINCIPAL_ASSIGNEES),
        verifiers=unicode(roles.AUDITORS),
        status=unicode(object_states.DRAFT),
        template_object_type=objects.get_obj_type(objects.CONTROLS))
    if is_add_rest_attrs:
      elements = element.CommonAudit
      asmt_tmpl_obj.update_attrs(
          default_people={
              "assignees": asmt_tmpl_obj.assignees,
              "verifiers": asmt_tmpl_obj.verifiers},
          people_values=[{"value": v, "title": t} for v, t in [
              (roles.ADMIN, elements.OBJECT_ADMINS),
              (roles.AUDIT_LEAD, elements.AUDIT_CAPTAIN),
              (roles.AUDITORS, elements.AUDITORS),
              (roles.PRINCIPAL_ASSIGNEES, elements.PRINCIPAL_ASSIGNEES),
              (roles.SECONDARY_ASSIGNEES, elements.SECONDARY_ASSIGNEES),
              (roles.PRIMARY_CONTACTS, elements.PRIMARY_CONTACTS),
              (roles.SECONDARY_CONTACTS, elements.SECONDARY_CONTACTS),
              (roles.OTHER, elements.OTHERS)]])
    return asmt_tmpl_obj


class AssessmentsFactory(EntitiesFactory):
  """Factory class for Assessments entities."""

  def __init__(self):
    super(AssessmentsFactory, self).__init__(objects.ASSESSMENTS)
    self.admins = [users.current_user()]
    self._acl_roles = [
        ("creators", roles.ACLRolesIDs.ASSESSMENT_CREATORS,
         [users.current_user()]),
        ("assignees", roles.ACLRolesIDs.ASSESSMENT_ASSIGNEES,
         [users.current_user()]),
        ("verifiers", roles.ACLRolesIDs.ASSESSMENT_VERIFIERS, [])
    ]

  def obj_inst(self):
    """Create Assessment object's instance and set values for attributes:
    type, verified, status.
    """
    return self.obj_entity_cls().update_attrs(
        is_allow_none=False, type=self.obj_type, verified=False,
        status=unicode(object_states.NOT_STARTED))

  def generate(self, mapped_objects, audit, asmt_tmpl=None):
    """Generate Assessment objects' instances under 'audit' based on info
    about 'mapped_objects' and 'asmt_tmpl' use generation logic accordingly.
    """
    mapped_objects = help_utils.convert_to_list(mapped_objects)
    asmts_creators = PeopleFactory.extract_people_emails(self.admins)
    asmts_assignees = audit.audit_captains
    asmts_verifiers = (
        audit.auditors if audit.auditors else audit.audit_captains)
    asmts_cas_def = None
    asmts_type = (
        mapped_objects[0].type
        if all(getattr(mapped_obj, "type") for mapped_obj in mapped_objects)
        else None)
    if asmt_tmpl:
      if asmts_type != asmt_tmpl.template_object_type:
        raise ValueError(
            "Mapped objects' type: {} have to be the same with Assessment "
            "Template's type: {}".format(
                asmts_type, asmt_tmpl.template_object_type))
      # if assignees or verifiers are ids (int not str related attrs)
      # todo add logic to converts ids (int) repr to users' names
      if any(all(isinstance(user, int) for user in asmts_users)
             for asmts_users in
             [asmts_users for asmts_users in asmts_assignees, asmts_verifiers
              if isinstance(asmts_users, list)]):
        raise NotImplementedError
      if asmt_tmpl.assignees == unicode(roles.AUDITORS):
        asmts_assignees = audit.auditors
      if asmt_tmpl.verifiers != unicode(roles.AUDITORS):
        asmts_verifiers = audit.audit_captains

      if getattr(asmt_tmpl, "custom_attribute_definitions"):
        asmts_cas_def = asmt_tmpl.custom_attribute_definitions
    asmts_objs = [
        empty_asmt.update_attrs(
            title=mapped_object.title + " assessment for " + audit.title,
            audit=audit.title, mapped_objects=[mapped_object],
            creators=asmts_creators, assignees=asmts_assignees,
            verifiers=asmts_verifiers, assessment_type=asmts_type,
            custom_attribute_definitions=asmts_cas_def
        ) for empty_asmt, mapped_object
        in zip([self.obj_inst() for _ in xrange(len(mapped_objects))],
               mapped_objects)]
    return asmts_objs

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Assessment entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    asmt_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        status=unicode(object_states.NOT_STARTED),
        assessment_type=objects.get_obj_type(objects.CONTROLS), verified=False)
    if is_add_rest_attrs:
      asmt_obj.update_attrs(
          recipients=",".join((
              unicode(roles.ASSIGNEES), unicode(roles.CREATORS),
              unicode(roles.VERIFIERS))))
    return asmt_obj


class IssuesFactory(EntitiesFactory):
  """Factory class for Issues entities."""

  def __init__(self):
    super(IssuesFactory, self).__init__(objects.ISSUES)
    self._acl_roles = [
        ("admins", roles.ACLRolesIDs.ISSUE_ADMINS, [users.current_user()])
    ]

  def _create_random_obj(self, is_add_rest_attrs):
    """Create Issue entity with randomly and predictably filled fields, if
    'is_add_rest_attrs' then add attributes for REST."""
    issue_obj = self.obj_inst().update_attrs(
        title=self.obj_title, slug=self.obj_slug,
        status=unicode(object_states.DRAFT),
        os_state=unicode(element.ReviewStates.UNREVIEWED))
    if is_add_rest_attrs:
      issue_obj.update_attrs(
          recipients=",".join((
              unicode(roles.ADMIN), unicode(roles.PRIMARY_CONTACTS),
              unicode(roles.SECONDARY_CONTACTS))))
    return issue_obj
