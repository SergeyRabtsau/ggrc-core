from lib.decorator import track_time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class ApiClient(object):
  def __init__(self, session):
    adapter = HTTPAdapter(max_retries=Retry(
      total=30, backoff_factor=0.5, status_forcelist=[503]))
    session.mount('http://', adapter)
    self.session = session

  @track_time
  def get(self, url, **kwargs):
    return self.session.get(url, **kwargs)

  @track_time
  def post(self, url, **kwargs):
    return self.session.post(url, **kwargs)
