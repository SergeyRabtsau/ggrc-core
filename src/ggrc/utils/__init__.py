# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

import logging
import datetime
import json
import re
import sys
import sqlalchemy

from flask import request
from ggrc.settings import CUSTOM_URL_ROOT
from ggrc.utils import benchmarks


logger = logging.getLogger()

DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_US = "%m/%d/%Y"


class GrcEncoder(json.JSONEncoder):

  """Custom JSON Encoder to handle datetime objects and sets

  from:
     `http://stackoverflow.com/questions/12122007/python-json-encoder-to-support-datetime`_
  also consider:
     `http://hg.tryton.org/2.4/trytond/file/ade5432ac476/trytond/protocols/jsonrpc.py#l53`_
  """

  def default(self, obj):
    from ggrc.models import mixins
    if isinstance(obj, datetime.datetime):
      if not obj.time():
        return obj.date().isoformat()
      return obj.isoformat()
    elif isinstance(obj, datetime.date):
      return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
      return (datetime.datetime.min + obj).time().isoformat()
    elif isinstance(obj, set):
      return list(obj)
    elif isinstance(obj, mixins.Base):
      return {"id": obj.id, "type": obj.type}
    elif callable(obj):
      return obj()
    else:
      return super(GrcEncoder, self).default(obj)


def as_json(obj, **kwargs):
  return json.dumps(obj, cls=GrcEncoder, **kwargs)


def service_for(obj):
  module = sys.modules['ggrc.services']
  if type(obj) is str or type(obj) is unicode:  # noqa
    model_type = obj
  else:
    model_type = obj.__class__.__name__
  return getattr(module, model_type, None)


def url_for(obj, id=None):
  service = service_for(obj)
  if service is None:
    return None
  if not hasattr(service, 'url_for'):
    return None
  if id is not None:
    return service.url_for(id=id)
  return service.url_for(obj)


def view_service_for(obj):
  module = sys.modules['ggrc.views']
  if type(obj) is str or type(obj) is unicode:  # noqa
    model_type = obj
  else:
    model_type = obj.__class__.__name__
  return getattr(module, model_type, None)


def view_url_for(obj, id=None):
  service = view_service_for(obj)
  if service is None:
    return None
  if not hasattr(service, 'url_for'):
    return None
  if id is not None:
    return service.url_for(id=id)
  return service.url_for(obj)


def encoded_dict(in_dict):
  # http://stackoverflow.com/questions/6480723/urllib-urlencode-doesn't-like-unicode-values-how-about-this-workaround
  out_dict = {}
  for k, v in in_dict.iteritems():
    if isinstance(v, unicode):  # noqa
      v = v.encode('utf8')
    elif isinstance(v, str):
      # Must be encoded in UTF-8
      v.decode('utf8')
    out_dict[k] = v
  return out_dict


def merge_dict(destination, source, path=None):
  """Merge source into destination.

  This function prevent creation of duplicates during merging as
  any subdict in destination related to unique key (user_email,
  notification_id, ParentObjInfo, ...). Merging duplicated value will
  be ignored.

  Args:
      destination: Dict in which we want to merge data. It can contain only
          dicts or simple types as values.
      source: Dict that should be merged. It can contain only
          dicts or simple types as values.
      path: List with keys to any node of source (only for internal usage).

  Returns:
      Dict with data combination from destination and source.
  """
  if path is None:
    path = []
  for key in source:
    if key in destination:
      if isinstance(destination[key], dict) and isinstance(source[key], dict):
        merge_dict(destination[key], source[key], path + [str(key)])
      elif destination[key] == source[key]:
        pass  # same leaf value
      else:
        # raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        # if merging does not work we should just log the warning instead of
        # raising an error and so sent out whatever notifications we can. This
        # might cause some data to be missing from the notifications themselves
        # but at least they will be sent
        logger.warning('Conflict at %s', '.'.join(path + [str(key)]))
    else:
      destination[key] = source[key]
  return destination


def merge_dicts(*args):
  result = {}
  for arg in args:
    result = merge_dict(result, arg)
  return result


def get_url_root():
  if CUSTOM_URL_ROOT:
    return CUSTOM_URL_ROOT
  return request.url_root


def _prefix_camelcase(name, prefix):
  name = name[:1].lower() + name[1:]
  return re.sub(r'[A-Z]', lambda pat: prefix + pat.group(0).lower(), name)


def underscore_from_camelcase(name):
  return _prefix_camelcase(name, "_")


def title_from_camelcase(name):
  return _prefix_camelcase(name, " ")


def get_fuzzy_date(delta_date):
  """Get a human readable date string.

  This function returns a human friendly time delta compared to today.

  Args:
    delta_date (date): Date that we want to show to the user.

  Returns:
    string: A human readable representation date delta.

  Examples:
    >>> get_fuzzy_date(datetime.date.today() + datetime.timedelta(2))
    'in 2 days'
    >>> get_fuzzy_date(datetime.date.today())
    'today'
    >>> get_fuzzy_date(datetime.date.today() + datetime.timedelta(-1))
    '1 day ago'
  """
  if not delta_date:
    return ""
  if isinstance(delta_date, datetime.datetime):
    delta_date = delta_date.date()
  delta = delta_date - datetime.date.today()
  if delta.days < 0:
    days = abs(delta.days)
    return "{} day{} ago".format(days, "s" if days > 1 else "")
  if delta.days == 0:
    return "today"
  # TODO: use format_timedelta from babel package.
  return "in {} day{}".format(delta.days, "s" if delta.days > 1 else "")


def get_digest_date_statement(delta_date, word, is_change_tense=False):
  """Get statement created from word in appropriate tense and readable date.

  This function returns phrase created using concatenation of a word in
  appropriate tense with human readable date value.

  Args:
    delta_date (date): Date that we want to show to the user
    word (str): With which date should be concatenated
    is_change_tense: Flag which shows is tense of the word should be changed

  Returns:
    string: A human readable statement, created from word and date
            concatenation
  """
  fuzzy_date = get_fuzzy_date(delta_date)
  word_end = ''
  if is_change_tense:
    if "in" in fuzzy_date:
      word_end = 's'
    else:
      word_end = 'ed'
  return '{}{} {}'.format(word, word_end, fuzzy_date)


# pylint: disable=too-few-public-methods
# because this is a small context manager
class QueryCounter(object):
  """Context manager for counting sqlalchemy database queries.

  Usage:
    with QueryCounter() as counter:
      query_count = counter.get
  """

  def __init__(self):
    self.queries = []

    def after_cursor_execute(*args):
      self.queries.append(args[2])

    self.listener = after_cursor_execute

  def __enter__(self):
    sqlalchemy.event.listen(sqlalchemy.engine.Engine,
                            "after_cursor_execute",
                            self.listener)
    return self

  def __exit__(self, *_):
    sqlalchemy.event.remove(sqlalchemy.engine.Engine,
                            "after_cursor_execute",
                            self.listener)

  @property
  def get(self):
    return len(self.queries)


benchmark = benchmarks.get_benchmark()


def convert_date_format(date, format_from, format_to):
  """Convert string date format from one to another."""
  return datetime.datetime.strptime(date, format_from).strftime(format_to)


def iso_to_us_date(date_string):
  """Convert date string from ISO format to US format."""
  return convert_date_format(date_string, DATE_FORMAT_ISO, DATE_FORMAT_US)


def generate_query_chunks(query, chunk_size=1000):
  """Make a generator splitting `query` into chunks of size `chunk_size`."""
  count = query.count()
  for offset in range(0, count, chunk_size):
    yield query.order_by("id").limit(chunk_size).offset(offset)


def create_stub(object_, context_id=None):
  """Create stub from model attribute

  Args:
    object_: Object instance
  Returns:
    Dict representation of stub
  """
  import ggrc.models as models

  if object_:
    id_ = object_.id
    type_ = object_.type

    model = getattr(models.all_models, type_)
    return {
        'type': type_,
        'id': id_,
        'context_id': context_id,
        'href': u"/api/{}/{}".format(model._inflector.table_plural, id_),
    }
  return None
