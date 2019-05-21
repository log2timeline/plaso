# -*- coding: utf-8 -*-
"""The event filter expression parser value expander classes."""

from __future__ import unicode_literals

import logging

from plaso.filters import helpers
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import py2to3


class EventValueExpander(object):
  """Value expander for event filters."""

  _FIELD_SEPARATOR = '.'

  def _GetMessage(self, event):
    """Retrieves a formatted message string.

    Args:
      event (EventObject): event.

    Returns:
      str: formatted message string.
    """
    # TODO: move this somewhere where the mediator can be instantiated once.
    formatter_mediator = formatters_mediator.FormatterMediator()

    result = ''
    try:
      result, _ = formatters_manager.FormattersManager.GetMessageStrings(
          formatter_mediator, event)
    except KeyError as exception:
      logging.warning(
          'Unable to correctly assemble event with error: {0!s}'.format(
              exception))

    return result

  def _GetSources(self, event):
    """Retrieves a formatted source strings.

    Args:
      event (EventObject): event.

    Returns:
      tuple(str, str): short and long source string.
    """
    try:
      # TODO: refactor to pass event and event_data as separate arguments.
      source_short, source_long = (
          formatters_manager.FormattersManager.GetSourceStrings(event, event))
    except KeyError as exception:
      logging.warning(
          'Unable to correctly assemble event with error: {0!s}'.format(
              exception))

    return source_short, source_long

  def _GetValue(self, obj, attr_name):
    """Retrieves the value of a specific object attribute.

    Args:
      obj (object): object to retrieve the value from.
      attr_name (str): name of the attribute to retrieve the value from.

    Returns:
      object: attribute value.
    """
    ret = getattr(obj, attr_name, None)

    if ret:
      if isinstance(ret, dict):
        ret = helpers.DictObject(ret)

      if attr_name == 'tag':
        return ret.labels

      return ret

    # Check if this is a message request and we have a regular EventObject.
    if attr_name == 'message':
      return self._GetMessage(obj)

    # Check if this is a source_short request.
    if attr_name in ('source', 'source_short'):
      source_short, _ = self._GetSources(obj)
      return source_short

    # Check if this is a source_long request.
    if attr_name in ('source_long', 'sourcetype'):
      _, source_long = self._GetSources(obj)
      return source_long

    return None

  def Expand(self, obj, path):  # pylint: disable=missing-type-doc
    """Retrieves the attribute values from an object given an object path.

    Given a path such as ["sub1", "sub2"] it returns all the values available
    in obj.sub1.sub2 as a list. sub1 and sub2 must be data attributes or
    properties.

    If sub1 returns a list of objects, or a generator, Expand aggregates the
    values for the remaining path for each of the objects, thus returning a
    list of all the values under the given path for the input object.

    Args:
      obj (object): object that will be traversed.
      path (str|list[str]): object path to traverse, that contains the attribute
          names.

    Yields:
      object: attribute value.
    """
    if isinstance(path, py2to3.STRING_TYPES):
      path = path.split(self._FIELD_SEPARATOR)

    attr_name = path[0].lower()

    attr_value = self._GetValue(obj, attr_name)
    if attr_value is not None:
      if len(path) == 1 or isinstance(attr_value, dict):
        yield attr_value

      else:
        try:
          for sub_obj in iter(attr_value):
            for value in self.Expand(sub_obj, path[1:]):
              yield value

        except TypeError:
          for value in self.Expand(attr_value, path[1:]):
            yield value
