# Copyright (C) 2018 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
from .exceptions import ValidationError


def validate_option(model, attribute, option, desired_role):
  if option and option.role != desired_role:
    message = ("Invalid value for attribute {}.{}. "
               "Expected option with role {}, received role {}."
               .format(model, attribute, desired_role, option.role))
    raise ValidationError(message)
  return option


class PolymorphicRelationship(object):
  """This is shortcut to generate relationships from type and id fields."""
  # pylint: disable=too-few-public-methods

  def __init__(self, id_attr, type_attr, backref_format):
    self._id_attr = id_attr
    self._type_attr = type_attr
    self._backref_format = backref_format

  def _make_backref_attr(self, obj):
    """Construct the name of backref attr from format and type field value."""
    return self._backref_format.format(getattr(obj, self._type_attr))

  def __get__(self, obj, cls):
    """Get the value of the backref attr."""
    if obj is None:
      return self
    else:
      return getattr(obj, self._make_backref_attr(obj))

  def __set__(self, obj, value):
    """Prepare and set the value of the backref attr."""
    if value is None:
      setattr(obj, self._id_attr, None)
      setattr(obj, self._type_attr, None)
    else:
      setattr(obj, self._id_attr, value.id)
      setattr(obj, self._type_attr, value.__class__.__name__)
      setattr(obj, self._make_backref_attr(obj), value)


class FasadeProperty(object):

  FIELD_NAME = None

  def __init__(self):
    assert self.FIELD_NAME

  def __call__(self, obj, json_obj):
    return self.prepare(json_obj)

  def prepare(self, data):
    return data

  def __set__(self, obj, value):
    setattr(obj, self.FIELD_NAME, value)
