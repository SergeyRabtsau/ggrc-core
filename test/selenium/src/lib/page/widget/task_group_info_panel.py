# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Task Group info panel."""
from lib import base
from lib.app_entity_factory import entity_factory_common
from lib.element import three_bbs
from lib.page.widget import table_with_headers
from lib.utils import selenium_utils, ui_utils


class TaskGroupInfoPanel(base.WithBrowser):
  """Represents Task Group info panel on Workflow Setup tab."""

  def __init__(self):
    super(TaskGroupInfoPanel, self).__init__()
    self._root = self._browser
    self._table = table_with_headers.TableWithHeaders(
        self._root,
        header_elements=self._task_header_elements,
        table_rows=self.task_rows
    )
    self._create_task_button = self._root.link(text="Create Task")

  def wait_to_be_init(self):
    """Wait for panel to be initialized."""
    self._create_task_button.wait_until(lambda e: e.present)
    ui_utils.wait_for_spinner_to_disappear()

  @property
  def _three_bbs(self):
    """Returns three bbs element."""
    return three_bbs.ThreeBbs(self._root.element(
        class_name="pane-header__toolbar"))

  def click_to_edit(self):
    """Clicks to edit task group."""
    self._three_bbs.option_by_text("Edit Task Group").click()

  def click_add_obj(self):
    """Clicks `Add Object` button."""
    self._root.link(text="Add Object").click()

  @property
  def added_objs(self):
    """Returns objects added to the task group."""
    prefix = "fa-"
    objs = []
    selenium_utils.wait_for_js_to_load(self._driver)
    obj_rows = (self._root.element(class_name="tree-structure").lis(
        class_name="task-group-objects__list-item"))
    for obj_row in obj_rows:
      # define object type by icon class
      icon = obj_row.element(tag_name="i").wait_until(lambda e: e.present)
      obj_name = [
        item.replace(prefix,"")
        for item in icon.classes
        if item.startswith(prefix) and item != prefix + "fw"][0]
      obj_title = obj_row.text
      factory = entity_factory_common.get_factory_by_obj_name(obj_name)()
      objs.append(factory.create_empty(title=obj_title))
    return objs

  def _task_header_elements(self):
    """Returns task header elements."""
    return self._root.elements(class_name="task_group_tasks__header-item")

  def task_rows(self):
    """Returns task rows."""
    return [TaskRow(row, self._table.table_header_names())
            for row in self._root.elements(class_name="object-list__item")]

  def click_create_task(self):
    """Clicks Create Task button."""
    self._create_task_button.click()


class TaskRow(object):
  """Represents task row in info panel."""

  def __init__(self, row_el, header_names):
    self._table_row = table_with_headers.TableRow(
        container=row_el,
        table_header_names=header_names,
        cell_locator={"class_name": "task_group_tasks__list-item-column"}
    )

  @property
  def assignees(self):
    """Returns list of assignees."""
    return [el.text for el in self._table_row.cell_for_header(
        "Task Assignees").elements(class_name="tree-field__item")]

  @property
  def start_date(self):
    """Returns start date."""
    return self._initial_setup.split(" - ")[0].strip()

  @property
  def due_date(self):
    """Returns due date."""
    return self._initial_setup.split(" - ")[1].strip()

  def obj_dict(self):
    """Returns object dictionary for the row."""
    dict_keys = ["title", "assignees", "start_date", "due_date"]
    return self._table_row.obj_dict(self, dict_keys)

  @property
  def _initial_setup(self):
    """Returns text of initial setup cell."""
    return self._table_row.text_for_header("Initial Setup")
