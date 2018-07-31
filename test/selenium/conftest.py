# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""PyTest fixtures."""
# pylint: disable=invalid-name
# pylint: disable=global-variable-not-assigned
# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
import logging
import os
import urlparse

import pytest
# Wokaround https://github.com/pytest-dev/pytest/issues/3775
from pytest_selenium import pytest_selenium as pt_selenium
from selenium.webdriver.remote.remote_connection import (
    LOGGER as SELENIUM_LOGGER)

from lib import dynamic_fixtures, environment, url, users
from lib.constants.test_runner import DESTRUCTIVE_TEST_METHOD_PREFIX
from lib.custom_pytest_scheduling import CustomPytestScheduling
from lib.entities import entities_factory
from lib.page import dashboard
from lib.service import rest_service, rest_facade
from lib.utils import conftest_utils, help_utils, selenium_utils
from lib.utils.selenium_utils import get_full_screenshot_as_base64


def pytest_xdist_make_scheduler(config, log):
  """Set the test scheduler for Pytest-xdist to a custom scheduler"""
  return CustomPytestScheduling(config, log)


def pytest_runtest_setup(item):
  """Set test variables that depend on dev server used
  (`dev` or `dev_destructive`):
  * environment.app_url
  * dev_log_retriever
  """
  if DESTRUCTIVE_TEST_METHOD_PREFIX in item.name:
    environment.app_url = os.environ["DEV_DESTRUCTIVE_URL"]
    filename = os.environ["DEV_DESTRUCTIVE_LOG"]
  else:
    environment.app_url = os.environ["DEV_URL"]
    filename = os.environ["DEV_LOG"]
  environment.app_url = urlparse.urljoin(environment.app_url, "/")
  #item.dev_log_retriever = conftest_utils.DevLogRetriever(filename)


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
  """Add dev server log as an extra link to HTML report"""
  outcome = yield
  report = outcome.get_result()
  extra = getattr(report, "extra", [])
  xfail = hasattr(report, "wasxfail")
  failure = (report.skipped and xfail) or (report.failed and not xfail)
  pytest_html = item.config.pluginmanager.getplugin("html")
  has_dev_log_retriever = hasattr(item, "dev_log_retriever")
  if failure and pytest_html is not None and has_dev_log_retriever:
    dev_logs = item.dev_log_retriever.get_added_logs()
    extra.append(pytest_html.extras.text(dev_logs, "Dev Server Log"))
  report.extra = extra


def patch_pytest_selenium_screenshot():
  """Patch pytest-selenium's _gather_screenshot function to make screenshot
  of the full page."""
  # pylint: disable=protected-access

  def gather_screenshot(item, report, driver, summary, extra):
    """Add link to the screenshot of the full page to HTML report"""
    try:
      # Only below line is changed
      screenshot = get_full_screenshot_as_base64(driver)
    except Exception as e:
      summary.append('WARNING: Failed to gather screenshot: {0}'.format(e))
      return
    pytest_html = item.config.pluginmanager.getplugin('html')
    if pytest_html is not None:
      extra.append(pytest_html.extras.image(screenshot, 'Screenshot'))

  pt_selenium._gather_screenshot = gather_screenshot


patch_pytest_selenium_screenshot()


def pytest_addoption(parser):
  """Add support for headless option to pytest-selenium."""
  parser.addoption('--headless',
                   action='store',
                   help='enable headless mode for supported browsers.')


# Disable selenium's remote_connection.py DEBUG statements that pollute
# test stdout.
# They aren't needed as driver logs are included into links of HTML report.
SELENIUM_LOGGER.setLevel(logging.INFO)


@pytest.fixture(autouse=True)
def reset_dict_executed_fixtures():
  """Reset dict_executed_fixtures between tests"""
  dynamic_fixtures.dict_executed_fixtures = {}


@pytest.fixture(scope="session")
def session_capabilities(session_capabilities):
  """Log browser (console log) and performance (request / response headers)
  data.
  They will appear in `Links` section of pytest-html's html report.
  """
  session_capabilities["loggingPrefs"] = {
      "browser": "ALL",
      "performance": "ALL"
  }
  return session_capabilities


@pytest.fixture(scope="function")
def selenium(selenium, pytestconfig):
  """Create Web Driver instance."""
  if not selenium_utils.is_headless_chrome(pytestconfig):
    selenium.set_window_size(
        os.environ["SCREEN_WIDTH"], os.environ["SCREEN_HEIGHT"])
  dynamic_fixtures.dict_executed_fixtures.update({"selenium": selenium})
  yield selenium


@pytest.fixture(scope="function")
def create_tmp_dir(tmpdir_factory, request):
  """Create temporary directory for test and return unconditional full path to
  it according to the next rule:
  selenium/tmp/'name of test method with parameters'.
  Example:
  Test's path to run:
  selenium/src/tests/test_audit_page.py::TestAuditPage::()::
  test_asmts_generation[Assessments generation without Assessment Template]
  Test's temp directory:
  selenium/tmp/
  test_asmts_generation[Assessments generation without Assessment Template]
  """
  test_name = request.node.name
  test_tmp_dir = tmpdir_factory.mktemp(test_name, numbered=True)
  yield test_tmp_dir.strpath


@pytest.fixture
def chrome_options(chrome_options, pytestconfig):
  """Set configuration to run Chrome with specific options."""
  if selenium_utils.is_headless_chrome(pytestconfig):
    chrome_options.set_headless(True)
    chrome_options.add_argument("window-size={},{}".format(
        os.environ["SCREEN_WIDTH"], os.environ["SCREEN_HEIGHT"]))
  return chrome_options


# `PeopleFactory.superuser` uses `environment.app_url` and `current user`.
# It is used in @pytest.mark.parametrize parameters.
# Parametrize parameters are evaluated before fixtures so
# `environment.app_url` and `current user` should be already set.
environment.app_url = os.environ["DEV_URL"]
environment.app_url = urlparse.urljoin(environment.app_url, "/")
users.set_current_user(users.FakeSuperUser())


@pytest.fixture(autouse=True)
def set_superuser_as_current_user():
  """Set super user as a current user"""
  # pylint: disable=protected-access
  users._current_user = users.FakeSuperUser()
  users.set_current_user(entities_factory.PeopleFactory.superuser)


@pytest.fixture(autouse=True)
def reset_logged_in_users():
  """Reset cache of logged in users.
  This cache is used to check if user has already logged in.
  """
  users.reset_logged_in_users()


# Legacy app fixtures

def _common_fixtures(fixture):
  """Generate common fixtures and return global dictionary of executed
  common fixtures.
  """
  dynamic_fixtures.generate_common_fixtures(fixture)
  if isinstance(fixture, tuple):
    fixture, _ = fixture
  fixture = dynamic_fixtures.dict_executed_fixtures[fixture]
  return (help_utils.get_single_obj(fixture)
          if not help_utils.is_multiple_objs(fixture) else fixture)


def _snapshots_fixtures(fixturename):
  """Generate snapshot fixtures used generation of common fixtures and return
  dictionary of executed common fixtures in scope of snapshot fixtures.
  """
  return dynamic_fixtures.generate_snapshots_fixtures(fixturename)


@pytest.fixture(scope="function")
def my_work_dashboard(selenium):
  """Open My Work Dashboard URL and
  return My Work Dashboard page objects model."""
  selenium_utils.open_url(selenium, url.Urls().dashboard)
  return dashboard.Dashboard(selenium)


@pytest.fixture(scope="function")
def header_dashboard(selenium):
  """Open My Work Dashboard URL and
  return Header Dashboard page objects model."""
  selenium_utils.open_url(selenium, url.Urls().dashboard)
  return dashboard.Header(selenium)


@pytest.fixture(scope="function")
def new_program_ui(selenium, request):
  """Create new Program object via UI (LHN).
  Return: (Program modal, Program Info widget).
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_org_group_ui(selenium, request):
  """Create new Org Group object via UI (LHN).
  Return: lib.page.widget.OrgGroupInfo
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_risk_ui(selenium, request):
  """Create new Risk Group object via UI (LHN).
  Return: lib.page.widget.Risks
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_program_rest(request):
  """Create new Program object via REST API.
  Return: lib.entities.entity.ProgramEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_programs_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.ProgramEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_control_rest(request):
  """Create new Control object via REST API.
  Return: lib.entities.entity.ControlEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_controls_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.ControlEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_controls_rest_snapshot(request):
  """Return snapshots of Controls objects via REST API.
  Return: [lib.entities.entity.ControlEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_objective_rest(request):
  """Create new Objective object via REST API.
  Return: lib.entities.entity.ObjectiveEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_objectives_rest(request):
  """Create new Objective objects via REST API.
  Return: [lib.entities.entity.ObjectiveEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_audit_rest(request):
  """Create new Audit under Program object via REST API.
  Return: lib.entities.entity.AuditEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_audits_rest(request):
  """Create new Controls objects via REST API.
  Return: [lib.entities.entity.AuditEntity, ...]
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_rest(request):
  """Create new Assessment under Audit object via REST API.
  Return: lib.entities.entity.AssessmentEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessments_rest(request):
  """Create new Assessments objects via REST API.
   Return: [lib.entities.entity.AssessmentEntity, ...]
   """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_issue_rest(request):
  """Create new Issue under Audit object via REST API.
  Return: lib.entities.entity.IssueEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_template_rest(request):
  """Create new Assessment Template under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessment_template_with_cas_rest(request):
  """Create new Assessment Template with CAs under Audit object via REST API.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_assessments_from_template_rest(request, new_audit_rest):
  """Create new Assessments based on Assessment Template via REST API.
  Return: [lib.entities.entity.AssessmentEntity, ...]
  """
  dict_executed_fixtures = dynamic_fixtures.dict_executed_fixtures
  control_snapshots = dynamic_fixtures.get_fixture_from_dict_fixtures(
      "new_controls_rest_snapshot")
  template = None
  for fixture_name in dict_executed_fixtures:
    if fixture_name.startswith("new_assessment_template"):
      template = dict_executed_fixtures[fixture_name][0]
  if not template:
    raise ValueError("Assessment template was not created")
  assessments_service = rest_service.AssessmentsFromTemplateService()
  assessments = assessments_service.create_assessments(
      audit=new_audit_rest,
      template=template,
      snapshots=control_snapshots
  )
  return assessments


@pytest.fixture(scope="function")
def new_cas_for_assessments_rest(request):
  """New global Custom Attributes for assessments created via REST API.
  Teardown - remove created gCAs.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def new_cas_for_controls_rest(request):
  """Create new Global Custom Attributes for Controls via REST API and
  delete GCAs as teardown section.
  """
  cas = _common_fixtures(request.fixturename)
  yield cas


@pytest.fixture(scope="function")
def create_audit_with_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program via REST API and return dictionary of executed fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def create_audit_with_control_and_update_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program, update Control via REST API and return dictionary of executed
  fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def create_audit_with_control_and_delete_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program, delete Control via REST API and return dictionary of executed
  fixtures.
  """
  yield _snapshots_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_objective_rest(request):
  """Map Objective to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_objectives_rest(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_programs_rest(request):
  """Map Programs to Control objects via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_control_rest_to_new_assessments_rest(request):
  """Map Assessments to Control via REST API return response from server."""
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_objective_rest(request):
  """Map Objective to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_control_rest(request):
  """Map Control to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_program_rest_to_new_controls_rest(request):
  """Map Controls to Program object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_assessment_rest_to_new_issue_rest(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


@pytest.fixture(scope="function")
def map_new_assessment_rest_to_new_control_rest_snapshot(request):
  """Map Objectives to Control object via REST API return response from server.
  """
  yield _common_fixtures(request.fixturename)


def _common_request_param(request):
  """Processing for common fixtures of request object which gives access to the
  requesting test context and has an optional param attribute in case the
  fixture is parametrized indirectly.
  """
  # todo implement '_snapshot_request_param'
  if hasattr(request, "param") and request.param:
    params = request.param
    return (({param: _common_fixtures(param) for param in params}
            if isinstance(params, list) else _common_fixtures(params)) if
            params else None)


@pytest.fixture(scope="function")
def dynamic_create_audit_with_control(request):
  """Create Program and Control, map Control to Program, create Audit
  under Program and dynamically make manipulations on Control (update,
  delete, ...) via REST API according to fixturename. Fixturename is indirect
  parameter that get from 'request.param' and have to be string or boolean.
  Return: lib.entities.entity.AssessmentTemplateEntity
  """
  if hasattr(request, "param") and request.param:
    yield (dynamic_fixtures.generate_snapshots_fixtures(request.param) if
           request.param else None)


@pytest.fixture(scope="function")
def dynamic_objects(request):
  """Create new object or objects via REST API or UI according to indirect
  parameter 'request.param' which can be: str, list of str, bool.
  Examples:
  - 'new_program_rest': lib.entities.entity.ProgramEntity;
  - 'new_programs_rest': [lib.entities.entity.ProgramEntity, ...];
  - ['new_program_rest', 'new_control_rest']:
    {'new_program_rest': lib.entities.entity.ProgramEntity,
     'new_control_rest': lib.entities.entity.ControlEntity};
  - True: None.
  """
  yield _common_request_param(request)


@pytest.fixture(scope="function")
def dynamic_objects_w_factory_params(request):
  """Create new object or objects via REST API or UI according to indirect
  parameter 'request.param' and w/ the same logic as 'dynamic_objects' fixture
  but using extra parameters to have option change default flow.
  """
  yield _common_request_param(request)


@pytest.fixture(scope="function")
def dynamic_relationships(request):
  """Create single or multiply relationships between source and destinations
  objects via REST API according to indirect parameter 'request.param' which
  can be: str, list of str, bool and return response or responses from server.
  Example:
  - 'map_new_program_rest_to_new_control_rest';
  - {'map_new_program_rest_to_new_control_rest': resp1,
     'map_new_control_rest_to_new_objective_rest': resp2}.
  """
  yield _common_request_param(request)


# New app fixtures

@pytest.fixture()
def program():
  """Create a program"""
  return rest_facade.create_program()


@pytest.fixture()
def issue_mapped_to_program(program):
  """Create an issue mapped to the program"""
  return rest_facade.create_issue(program)


@pytest.fixture()
def control_mapped_to_program(program):
  """Create a control mapped to the program"""
  return rest_facade.create_control(program)


@pytest.fixture()
def controls_mapped_to_program(program):
  """Create 2 controls mapped to the program"""
  return [rest_facade.create_control(program) for _ in xrange(2)]


@pytest.fixture()
def objective_mapped_to_program(program):
  """Create an objective mapped to the program"""
  return rest_facade.create_objective(program)


@pytest.fixture()
def objectives_mapped_to_program(program):
  """Create 2 objectives mapped to the program"""
  return [rest_facade.create_objective(program) for _ in xrange(2)]


@pytest.fixture()
def audit(program):
  """Create an audit within program"""
  return rest_facade.create_audit(program)


@pytest.fixture()
def audits(program):
  """Create 2 audits mapped to the program"""
  return [rest_facade.create_audit(program) for _ in xrange(2)]


@pytest.fixture()
def obj(request):
  """A fixture that calls any other fixture when parametrization
  with indirect is used.
  """
  return request.getfixturevalue(request.param)
