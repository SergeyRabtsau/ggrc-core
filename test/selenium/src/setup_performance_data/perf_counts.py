
stnd_count = 20
req_count = 500
clause_count = 50
reg_count = 2000
ctrl_count = 2000
objv_count = 2000
audit_count = 8
sys_count = 1000
proc_count = 500
product_count = 1000

prg_sizes = {"small": 0,
              "medium": 0,
              "large": 1}

rates = {"small": 0.25,
         "medium": 0.5,
         "large": 1}


class Counts(object):
  def __init__(self, size_name):
      self.sys = None
      self.proc = None
      self.product = None
      self._size_name = size_name
      self._rate = rates.get(size_name, 0.25)
      self.stnd =  self._get_rated_count(stnd_count)
      self.req = self._get_rated_count(req_count)
      self.clause = self._get_rated_count(clause_count)
      self.reg = self._get_rated_count(reg_count)
      self.ctrl = self._get_rated_count(ctrl_count)
      self.objv = self._get_rated_count(objv_count)
      self.audit = self._get_rated_count(audit_count)
      self.sys = self._get_rated_count(sys_count)
      self.proc = self._get_rated_count(proc_count)
      self.product = self._get_rated_count(product_count)


  def _get_rated_count(self, original_count):
    rated_count = int(original_count * self._rate)
    return rated_count if rated_count > 0 else 1


def get_list_of_counts():
  return [Counts(k) for k, v in prg_sizes.items() for _ in range(v)]


def get_list_of_codes():
  return {str(cur_value)+size_name: size_name
         for size_name, counts in
         prg_sizes.items()
         for cur_value in range(counts)}

