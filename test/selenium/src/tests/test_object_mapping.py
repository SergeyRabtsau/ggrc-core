# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Tests relevant to object mapping"""
# pylint: disable=no-self-use
# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods
# pylint: disable=unused-argument

import pytest

from lib import base
from lib import factory
from lib.page import dashboard
from lib.utils import conftest_utils
from lib.utils import selenium_utils


class TestObjectMapping(base.Test):
  """A part of smoke tests, section 4."""

  @pytest.mark.smoke_tests
  def test_mapping_via_lhn(self, selenium, new_product,
                           new_project, new_system, new_data_asset,
                           new_process):
    """LHN mapping tests from smoke tests, section 6"""
    objects = [new_product, new_project, new_system, new_data_asset,
               new_process]

    for object_ in objects:
      selenium.get(object_.url)
      header = dashboard.Header(selenium)

      # map objects
      for mapped_object in objects:
        # don't map an object to itself
        if mapped_object != object_:
          extended_info = conftest_utils\
              .get_lhn_accordion(selenium, mapped_object.object_name)\
              .hover_over_visible_member(mapped_object.title_entered.text)

          if not extended_info.is_mapped:
            extended_info.map_to_object()

            # workaround for CORE-3324
            selenium_utils.hover_over_element(
                selenium, header.toggle_user_dropdown.element)

            # close LHN so that the contents are seen
            header.close_lhn_menu()

            widget = factory.get_cls_widget(mapped_object.object_name)(
                selenium)

            # check that the focus is on relevant widget
            assert widget.name_from_url in mapped_object.object_name

            # check items count
            assert widget.member_count == 1

      # check that all mapped widgets are shown
      widget_bar = dashboard.Dashboard(selenium)

      for mapped_object in objects:
        if mapped_object != object_:
          # select a widget
          getattr(widget_bar,
                  factory.get_method_select(mapped_object.object_name))()

          # verify widget
          widget = factory.get_cls_widget(mapped_object.object_name)(
              selenium)
          assert widget.name_from_url in mapped_object.object_name
