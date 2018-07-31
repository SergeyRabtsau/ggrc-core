# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Export page with Export Panels."""

import os

from nerodia.wait.wait import TimeoutError
from waiting import TimeoutExpired

from lib import base
from lib.utils import selenium_utils, test_utils


class ExportItem(base.Component):
  """Export item on Export Page."""

  def __init__(self, driver, export_item_elem):
    super(ExportItem, self).__init__(driver)
    self.export_item_elem = export_item_elem

  def download_csv(self):
    el = self.export_item_elem.element(text="Download CSV")
    el.wait_until_present(timeout=12)  # to raise aa different error
    el.click()


class ExportPage(base.AbstractPage):
  """Export Page."""

  def __init__(self, driver):
    super(ExportPage, self).__init__(driver)
    self.export_page = self._browser.element(id="csv_export")
    self.add_obj_type_btn = self.export_page.element(text="Add Object Type")
    self.export_objs_btn = self.export_page.element(id="export-csv-button")

  def get_export_items(self):
    """Get the list of all Export Items which are present on Export Page."""
    # workaround for https://github.com/watir/watir/issues/759
    if not self.export_page.present:
      return []
    return [ExportItem(self._driver, export_item_elem) for export_item_elem in
            self.export_page.elements(class_name="current-exports__item")]

  def export_objs_to_csv(self, path_to_export_dir):
    """Click to 'Export Objects' button to export objects, wait for export,
    download as CSV and return path to the downloaded file.
    """
    export_items_before_count = len(self.get_export_items())
    self.export_objs_btn.click()

    def exported_item():
      """Return the export item that was just created."""
      difference = len(self.get_export_items()) - export_items_before_count
      if difference == 1:
        return self.get_export_items()[-1]
      return None
    selenium_utils.set_chrome_download_location(
        self._driver, path_to_export_dir)
    for i in xrange(0, 5):
      try:
        export_item = test_utils.wait_for(exported_item, timeout_seconds=12)
        downloads_before = os.listdir(path_to_export_dir)
        export_item.download_csv()
      except (TimeoutError, TimeoutExpired):
        self._browser.refresh()
        continue
      break

    def path_to_downloaded_file():
      """Path to a file that has appeared."""
      difference = set(os.listdir(path_to_export_dir)) - set(downloads_before)
      if len(difference) == 1:
        filename = list(difference)[0]
        return os.path.join(path_to_export_dir, filename)
      return None
    return test_utils.wait_for(path_to_downloaded_file)
