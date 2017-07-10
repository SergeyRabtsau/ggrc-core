# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Utility classes and functions for page objects used in tests.
Details:
Most of tests require sequence of primitive methods of page
object. If sequence repeats itself among tests, it should be shared in
this module.
"""
# pylint: disable=too-few-public-methods

import re
import uuid

from lib import base
from lib.constants.test import modal_create_new, modal_custom_attribute


def append_random_string(text):
  return text + str(uuid.uuid4())


def prepend_random_string(text):
  return str(uuid.uuid4()) + text


class HtmlParser(object):
  """The HtmlParser class simulates what happens with (non-rich)text in HTML.
 """
  @staticmethod
  def parse_text(text):
    """Simulates text parsed by html.
    Args: text (basestring)
    """
    return re.sub(r'\s+', " ", text)


class ModalInput(base.TestUtil):
  """Base class for filling out modals."""
  @staticmethod
  def enter_test_data(modal):
    modal.enter_title(append_random_string(modal_create_new.SHORT_TITLE))


class ModalNewControls(ModalInput):
  """Methods for simulating common user actions."""

  @staticmethod
  def enter_test_data(modal):
    """Fills out all fields in lhn_modal.
    Args: modal (lib.page.lhn_modal.new_control.Controls)
    """
    modal.enter_title(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_description(append_random_string(
        modal_create_new.SHORT_TITLE))
    modal.enter_test_plan(append_random_string(
        modal_create_new.SHORT_TITLE))
    modal.enter_notes(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_code(append_random_string(modal_create_new.SHORT_TITLE))


class ModalNewPrograms(ModalInput):
  """Methods for simulating common user actions."""

  @staticmethod
  def set_start_date(modal, day_start):
    """Sets start date from datepicker in new program/edit modal.
    Args:
    modal (lib.page.modal.edit_object.Programs)
    day_start (int): for more info see
    base.DatePicker.select_day_in_current_month
    """
    modal.enter_effective_date_start_month(day_start)

  @staticmethod
  def enter_test_data(modal):
    """Fills out all fields in lhn_modal.
    Args: modal (lib.page.modal.edit_object.Programs)
    """
    modal.enter_title(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_description(append_random_string(
        modal_create_new.SHORT_TITLE))
    modal.enter_notes(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_code(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_program_ref_url(prepend_random_string(
        modal_create_new.Programs.PROGRAM_URL))
    ModalNewPrograms.set_start_date(modal, 0)


class ModalNewProgramCustomAttribute(ModalInput):
  @staticmethod
  def enter_test_data(modal):
    """Fills out all fields in lhn_modal.
    Args: modal (lib.page.modal.custom_attribute.ModalCustomAttributes)
    """
    modal.enter_title(append_random_string(
        modal_custom_attribute.Programs.TITLE))
    modal.enter_inline_help(append_random_string(
        modal_custom_attribute.Programs.INLINE_HELP))
    modal.enter_placeholder(append_random_string(
        modal_custom_attribute.Programs.PLACEHOLDER))


class ModalNewOrgGroups(ModalInput):
  """Utils for data entry for Org Group modals."""


class ModalNewRisks(ModalInput):
  """Utils for data entry for Risk modals."""
  @staticmethod
  def enter_test_data(modal):
    """Fills out all fields in lhn_modal.
    Args: modal (lib.page.modal.edit_object.EditRisksModal)
    """
    modal.enter_title(append_random_string(modal_create_new.SHORT_TITLE))
    modal.enter_description(append_random_string(
        modal_create_new.SHORT_TITLE))


class ModalNewIssues(ModalInput):
  """Utils for data entry for Issues modals."""


class ModalNewProcesses(ModalInput):
  """Utils for data entry for Process modals."""


class ModalNewDataAssets(ModalInput):
  """Utils for data entry for Data asset modals."""


class ModalNewSystems(ModalInput):
  """Utils for data entry for System modals."""


class ModalNewProducts(ModalInput):
  """Utils for data entry for Product modals."""


class ModalNewProjects(ModalInput):
  """Utils for data entry for Project modals."""
