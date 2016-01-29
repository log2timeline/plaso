# -*- coding: utf-8 -*-
"""The storage collection information object."""

import collections

from plaso.lib import py2to3


class CollectionInformation(object):
  """Collection information object."""

  # This is a reserved keyword used among other things for serialization
  # of the collection information object. This is placed here to make sure it
  # is not used as a regular argument.
  # TODO: Should this be here or stored in the serialization library?
  RESERVED_COUNTER_KEYWORD = u'__COUNTERS__'

  def __init__(self):
    """Initialize the collection information object."""
    super(CollectionInformation, self).__init__()
    self._counters = {}
    self._value_dict = {}

  def AddCounter(self, identifier):
    """Add a counter to the collection information object.

    Args:
      identifier: name of the counter to be added.

    Raises:
      KeyError: if the counter has already been added or the identifier
                is not a string value.
    """
    if identifier in self._counters:
      raise KeyError(u'Counter [{0:s}] already added.'.format(identifier))

    if not isinstance(identifier, py2to3.STRING_TYPES):
      raise KeyError(u'Counter identifier [{0!s}] is not a string value.')

    self._counters[identifier] = collections.Counter()

  def AddCounterDict(self, identifier, counter_dict):
    """Add a counter to the collection information object.

    Args:
      identifier: name of the counter to be added.
      counter_dict: dictionary object that contains key/count values.

    Raises:
      KeyError: if the counter has already been added.
    """
    if identifier in self._counters:
      raise KeyError(u'Counter [{0:s}] already added.'.format(identifier))

    self._counters[identifier] = collections.Counter(counter_dict)

  def HasCounters(self):
    """Returns a boolean value indicating whether any counters are stored."""
    if self._counters:
      return True

    return False

  def GetCounter(self, identifier):
    """Retrieves a counter by an identifier.

    Args:
      identifier: the counter identifier.

    Returns:
      The counter (instance of collections.Counter) or None if not available.
    """
    return self._counters.get(identifier)

  def GetCounters(self):
    """Retrieves a list of all available counters.

    Returns:
      A list of tuples with two entries, identifier and a counter object
      (instance of collections.Counter) for all registered counters.
    """
    return self._counters.items()

  def GetValue(self, identifier, default_value=None):
    """Retrieves a value by identifier.

    Args:
      identifier: the value identifier.
      default_value: optional default value.

    Returns:
      The value or None if not available.
    """
    return self._value_dict.get(identifier, default_value)

  def GetValueDict(self):
    """Retrieves the set of stored values and identifiers as a dict."""
    return self._value_dict

  def GetValues(self):
    """Generates a list of all stored identifiers and values."""
    for identifier, value in self._value_dict.iteritems():
      yield identifier, value

  def IncrementCounter(self, identifier, element, value=1):
    """Increment a counter by value given an identifier.

    Args:
      identifier: the counter identifier.
      element: the counter element that is being incremented.
      value: optional integer denoting the value the counter is to
             be incremented with. Defaults to one.
    """
    if identifier not in self._counters:
      return

    self._counters[identifier][element] += value

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier: the value identifier.
      value: the value.

    Raises:
      ValueError: if a value is already set.
    """
    if identifier in self._value_dict:
      raise ValueError(u'Value for {0:s} is already set.'.format(identifier))

    if identifier == self.RESERVED_COUNTER_KEYWORD:
      raise ValueError(u'Unable to set the value, reserved identifier.')

    self._value_dict[identifier] = value

  def SetValues(self, values):
    """Sets values by a list of identifiers and their values.

    Args:
      values: a dict containing identifiers and values to be set.

    Raises:
      ValueError: if an identifier within the values already exists.
    """
    for identifier in values.iterkeys():
      if (identifier in self._value_dict or
          identifier == self.RESERVED_COUNTER_KEYWORD):
        raise ValueError(u'Value for {0:s} is already set.'.format(identifier))

    for identifier, value in values.iteritems():
      self._value_dict[identifier] = value
