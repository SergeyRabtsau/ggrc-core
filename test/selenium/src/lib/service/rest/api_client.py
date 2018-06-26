from lib.decorator import track_time


class ApiClient(object):
  def __init__(self, session):
    self.session = session

  @track_time
  def get(self, url, **kwargs):
    return self.session.get(url, **kwargs)

  @track_time
  def post(self, url, **kwargs):
    return self.session.post(url, **kwargs)
