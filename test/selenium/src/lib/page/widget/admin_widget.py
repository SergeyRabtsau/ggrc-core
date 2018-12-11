# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Widgets on Admin Dashboard page."""
# pylint: disable=too-few-public-methods

from lib import base, exception
from lib.constants import locator, objects
from lib.entities.entities_factory import PeopleFactory
from lib.page.widget import widget_base
from lib.utils import selenium_utils


class Widget(base.Widget):
  """Base class for Admin widgets."""


class Events(Widget):
  """Event widget on Admin Dashboard."""
  _locators = locator.WidgetAdminEvents

  def __init__(self, driver):
    super(Events, self).__init__(driver)
    self.widget_header = base.Label(driver, self._locators.TREE_VIEW_HEADER)

  def get_events(self):
    """Get list of elements that displayed in Tree View on Event widget."""
    selenium_utils.get_when_clickable(
        self._driver, self._locators.FIRST_TREE_VIEW_ITEM)
    self._browser.elements(class_name="event-owner")[0].element(
        class_name="person-name").wait_until(lambda e: "@" in e.text)
    return self._driver.find_elements(*self._locators.TREE_VIEW_ITEMS)


class People(Widget):
  """People widget on Admin Dashboard."""
  _locators = locator.WidgetAdminPeople

  def __init__(self, driver):
    super(People, self).__init__(driver)
    self.people_tree_view = base.AdminTreeView(self._driver)

  def get_people(self):
    """Get list of people that displayed in Tree View on People widget.
    """
    tree_view_items = self.people_tree_view.tree_view_items()
    people_as_lists = [item.text.splitlines() for item in tree_view_items]
    return [PeopleFactory().create(
        name=person[0], email=person[1], system_wide_role=person[2])
        for person in people_as_lists]

  def click_create_button(self):
    """Click on the Create button on People widget"""
    add_button = selenium_utils.get_when_clickable(
        self._driver, self._locators.CREATE_PERSON_BUTTON_SELECTOR)
    add_button.click()

  def filter_by_name_email_company(self, str_to_filter_by):
    """Filter people via filter by name email company text field"""
    filter_tf = base.TextInputField(
        self._driver, self._locators.FILTER_BY_NAME_EMAIL_COM_FIELD_SELECTOR)
    filter_tf.enter_text(str_to_filter_by)
    filter_tf.send_enter_key()
    selenium_utils.wait_for_js_to_load(self._driver)


class Roles(Widget):
  """Admin roles widget on Admin Dashboard."""

  def __init__(self, driver):
    super(Roles, self).__init__(driver)
    self.roles_tree_view = base.AdminTreeView(self._driver)

  def get_role_scopes_text_as_dict(self):
    """Get dictionary of labels that displayed in Tree View on Roles widget.
    """
    tree_view_items = self.roles_tree_view.tree_view_items()
    return dict([item.text.splitlines() for item in tree_view_items])


class CustomRoles(Widget):
  """Admin custom roles widget on Admin Dashboard."""

  def __init__(self, driver):
    super(CustomRoles, self).__init__(driver)
    self.custom_roles_tree_view = base.AdminTreeView(self._driver)

  def get_objects_text_as_set(self):
    """Get set of objects labels displayed in Tree View on Custom Roles widget.
    """
    tree_view_items = self.custom_roles_tree_view.tree_view_items()
    return set(item.text for item in tree_view_items)


class CustomAttributes(widget_base.WidgetAdminCustomAttributes):
  """Custom attributes widget on Admin Dashboard page."""

  def __init__(self, driver):
    super(CustomAttributes, self).__init__(driver)
    self.ca_tree_view = base.AdminTreeView(self._driver)

  def expand_collapse_group(self, item_title, expand=True):
    """Expand/collapse 2-nd tier of Tree View item."""
    items = self.get_items_list()
    for i in items:
      if i.text == item_title:
        if expand:
          return i.expand()
        return i.collapse()
    raise exception.ElementNotFound('{} in list {}'.format(item_title, items))

  def get_items_list(self):
    """Return Tree View item objects from current widget."""
    return self.ca_tree_view.tree_view_items()

  def add_custom_attribute(self, ca_obj):
    """Add custom attribute from custom attribute object given."""
    ca_item_content = self.expand_collapse_group(
        objects.get_normal_form(ca_obj.definition_type), expand=True)
    ca_item_content.add_new_custom_attribute(ca_obj)
    self.expand_collapse_group(
        objects.get_normal_form(ca_obj.definition_type), expand=False)

  def get_custom_attributes_list(self, ca_group):
    """Collect custom attributes from expanded custom attribute group
    Tree View.
    """
    ca_item_content = self.expand_collapse_group(
        objects.get_normal_form(ca_group.definition_type), expand=True)
    return ca_item_content.get_ca_list_from_group()


class ModalCustomAttributes(widget_base.CustomAttributeModal):
  """Custom attributes modal."""
