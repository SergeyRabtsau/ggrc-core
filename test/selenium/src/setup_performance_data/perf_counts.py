import collections

# initial constants
STND = 20
REQ = 500
CLAUSE = 50
REG = 2000
CTRL = 2000
OBJV = 2000
AUDIT = 8
SYS = 1000
PROC = 500
PROD = 1000
ASMT_TMPL = 1
ASMT_LCA = 10
ASMT_GCA = 5

# roles
PROGRAM_MANAGERS = 100
PROGRAM_EDITORS = 50
PROGRAM_READERS = 600
ADMINS = 30
PRIM_CONTACTS = 10
SEC_CONTACTS = 10
AUDIT_CAPTAIN = 20
AUDITOR = 200
ASMT_CREATOR = 20
ASMT_VERIFIER = 20
ASMT_ASSIGNEE = 20


# program pool
prg_sizes = collections.OrderedDict([
  ("large", 0),
  ("medium", 0),
  ("small", 0),
  ("xs", 1),
  ("xxs", 1)
])

rates = {
  "small": 0.25,
  "medium": 0.5,
  "large": 1,
  "xs": 0.2,
  "xxs": 0.1
}


def prg_index_list():
  """Return list indexes based on value for key, start from beging for new key.
  Example:
    [0, 0, 1, 2, 0]
  """
  return [
    item
    for k, v in prg_sizes.items()
    for item in range(v)
  ]


def prg_size_list():
  """Return list of sizes based on value for key.
  Example ['large', 'medium', 'medium', 'small']
  """
  return [
    item
    for k, v in prg_sizes.items()
    for item in [k] * v
  ]


class CoreObjectCounts(object):
  def __init__(self, size_name):
    """Create counts based on size, if size doens't exist in program pool
    then only one of type of each object will be specified.
    """
    self._size_name = size_name
    self._rate = rates.get(size_name, 0)
    self.stnd = self._get_rated_count(STND)
    self.req = self._get_rated_count(REQ)
    self.clause = self._get_rated_count(CLAUSE)
    self.reg = self._get_rated_count(REG)
    self.ctrl = self._get_rated_count(CTRL)
    self.objv = self._get_rated_count(OBJV)
    self.audit = self._get_rated_count(AUDIT)
    self.sys = self._get_rated_count(SYS)
    self.proc = self._get_rated_count(PROC)
    self.product = self._get_rated_count(PROD)
    # roles
    self.prg_mgr = self._get_rated_count(PROGRAM_MANAGERS)
    self.prg_editor = self._get_rated_count(PROGRAM_EDITORS)
    self.prg_reader = self._get_rated_count(PROGRAM_READERS)
    self.auditor = self._get_rated_count(AUDITOR)
    self.audit_cap = self._get_rated_count(AUDIT_CAPTAIN)
    self.admin = self._get_rated_count(ADMINS)
    self.prim_con = self._get_rated_count(PRIM_CONTACTS)
    self.sec_con = self._get_rated_count(SEC_CONTACTS)
    self.asmt_creator = self._get_rated_count(ASMT_CREATOR)
    self.asmt_assignee = self._get_rated_count(ASMT_ASSIGNEE)
    self.asmt_verifier = self._get_rated_count(ASMT_VERIFIER)

  @property
  def users_per_prg(self):
    return (self.prg_mgr + self.prg_editor + self.prg_reader + self.auditor
           + self.audit_cap + self.admin + self.prim_con + self.sec_con
           + self.asmt_creator + self.asmt_assignee + self.asmt_verifier)


  def _get_rated_count(self, original_count):
    rated_count = int(original_count * self._rate)
    return rated_count if rated_count > 0 else 1


def get_total_user_counts():
  return sum([
    CoreObjectCounts(k).users_per_prg
    for k, v in prg_sizes.items()
    for _ in range(v)
  ])

