# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
"""Pool to hold requests sessions."""

from lib import url as url_module

import requests

SESSION_COOKIE_VALUE = None


class SessionPool(object):
  """Pool to hold requests sessions."""

  BASIC_HEADERS = {'X-Requested-By': 'GGRC',
                   'Content-Type': 'application/json',
                   'Accept-Encoding': 'gzip, deflate, br'}

  def __init__(self):
    self._sessions = {}

  def get_session(self, user):
    """Return a requests Session for the `user`"""
    if user.email in self._sessions:
      return self._sessions[user.email]
    return self._create_session(user)

  def _create_session(self, user):
    """Create a new requests Session for the `user`"""
    session = requests.Session()
    session.headers = self.BASIC_HEADERS
    self._set_login_cookie(session, user)
    self._store_session(user, session)
    return session

  def _set_login_cookie(self, session, user):
    """Set dev_appserver_login and session cookies."""
    session.get(url_module.Urls().gae_login(user))
    session.get(url_module.Urls().login)

  def _store_session(self, user, session):
    """Store user's `session` in session pool"""
    self._sessions[user.email] = session
