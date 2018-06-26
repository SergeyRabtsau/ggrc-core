import itertools

from lib.decorator import memoize
from lib.service import rest_facade
import perf_const as const


class TestCreateData(object):
  """This is not really a test class.
  It was made a test to share DEV_URL from pytest.ini, environment.app_url
  and current user from conftest.py
  """

  def test_create_users(self):
    people = rest_facade.create_objs("people", const.USERS)
    for person in people:
      print person.email

  @memoize
  def users(self):
    return rest_facade.create_objs("people", const.USERS)

  @memoize
  def user_generator(self):
    return itertools.cycle(self.users())

  def next_items(self, iterable, n):
    return list(itertools.islice(iterable, n))

  def next_users(self, n):
    return self.next_items(self.user_generator(), n)

  def chunks_generator(self, iterable, chunk_size):
    """Return an iterator that returns `chunk_size` items from `iterable`
    in infinite loop
    """
    infinite_iter = itertools.cycle(iterable)
    while True:
      yield list(itertools.islice(infinite_iter, chunk_size))

  def add_mapped_asmt(self, audit, assessment_type, objs_to_map):
    """Create assessment with assessment type=`assessment_type` and
    map it to snapshots of `objs_to_map`"""
    assessment = rest_facade.create_assessment(
        audit, assessment_type=assessment_type)
    for obj in objs_to_map:
      rest_facade.map_to_snapshot(assessment, obj=obj, parent_obj=audit)
    assessment.update_attrs(mapped_objects=objs_to_map)
    return assessment

  def add_assessments(self, audit, all_controls):
    controls_generator = self.chunks_generator(all_controls, const.ASSESSMENT_CONTROLS)
    for _ in xrange(const.ASSESSMENT):
      objs_to_map = next(controls_generator)
      self.add_mapped_asmt(
          audit, assessment_type="Control", objs_to_map=objs_to_map)

  def add_objects_for_program(self, program):
    for _ in xrange(const.OBJECTIVE):
      rest_facade.create_objective(program)
    controls = [
        rest_facade.create_control(
            program,
            admins=self.next_users(const.CONTROL_ADMINS),
            primary_contacts=self.next_users(const.CONTROL_PRIMARY_CONTACTS))
        for _ in xrange(const.CONTROL)]
    audits = [rest_facade.create_audit(program) for _ in xrange(const.AUDIT)]
    for audit in audits:
      self.add_assessments(audit, controls)

# import timeit
#
#   def test_add_data(self):
#     programs = [
#         rest_facade.create_program(
#             managers=self.next_users(const.PROGRAM_MANAGERS),
#             editors=self.next_users(const.PROGRAM_EDITORS))
#         for _ in xrange(const.PROGRAM)]
#     for program in programs:
#       self.add_objects_for_program(program)

  def create_programs(self):
    return rest_facade.create_objs(
        "programs", const.PROGRAM,
        chunk_size = 10,
        managers=self.next_users(const.PROGRAM_MANAGERS),
        editors=self.next_users(const.PROGRAM_EDITORS),
        readers=self.next_users(const.PROGRAM_READERS))

  def test_create(self):
    programs = self.create_programs()
