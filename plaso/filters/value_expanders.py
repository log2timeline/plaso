# -*- coding: utf-8 -*-
"""The event filter expression parser value expander classes."""

from __future__ import unicode_literals

import abc
import logging

from plaso.filters import helpers
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import py2to3


class ValueExpander(object):
  """Value expander interface.

  The value expander contains the logic to expand values in an object.
  """

  FIELD_SEPARATOR = '.'

  def _GetAttributeName(self, path):
    """Retrieves the attribute name to fetch given a path.

    Args:
      path (list[str]): object path, that contains the attribute names.

    Returns:
      str: attribute name.
    """
    return path[0]

  @abc.abstractmethod
  def _GetValue(self, obj, attr_name):
    """Retrieves the value of a specific object attribute.

    Args:
      obj (object): object to retrieve the value from.
      attr_name (str): name of the attribute to retrieve the value from.

    Returns:
      object: attribute value.
    """

  def _AtLeaf(self, attr_value):
    """Retrieves the attribute value of a leaf node.

    Yields:
      object: attribute value.
    """
    yield attr_value

  def _AtNonLeaf(self, attr_value, path):
    """Retrieves the attribute value of a branch (non-leaf) node.

    Yields:
      object: attribute value.
    """
    try:
      # Check first for iterables
      # If it's a dictionary, we yield it
      if isinstance(attr_value, dict):
        yield attr_value
      else:
        # If it's an iterable, we recurse on each value.
        for sub_obj in attr_value:
          for value in self.Expand(sub_obj, path[1:]):
            yield value
    except TypeError:  # This is then not iterable, we recurse with the value
      for value in self.Expand(attr_value, path[1:]):
        yield value

  def Expand(self, obj, path):
    """Retrieves the attribute values from an object given an object path.

    Given a path such as ["sub1", "sub2"] it returns all the values available
    in obj.sub1.sub2 as a list. sub1 and sub2 must be data attributes or
    properties.

    If sub1 returns a list of objects, or a generator, Expand aggregates the
    values for the remaining path for each of the objects, thus returning a
    list of all the values under the given path for the input object.

    Args:
      obj (object): object that will be traversed.
      path (list[str]): object path to traverse, that contains the attribute
          names.

    Yields:
      object: attribute value.
    """
    if isinstance(path, py2to3.STRING_TYPES):
      path = path.split(self.FIELD_SEPARATOR)

    attr_name = self._GetAttributeName(path)
    attr_value = self._GetValue(obj, attr_name)
    if attr_value is None:
      return

    if len(path) == 1:
      for value in self._AtLeaf(attr_value):
        yield value
    else:
      for value in self._AtNonLeaf(attr_value, path):
        yield value


class AttributeValueExpander(ValueExpander):
  """Value expander that expands based on object attribute names."""

  def _GetValue(self, obj, attr_name):
    """Retrieves the value of a specific object attribute.

    Args:
      obj (object): object to retrieve the value from.
      attr_name (str): name of the attribute to retrieve the value from.

    Returns:
      object: attribute value or None if attribute is not available.
    """
    return getattr(obj, attr_name, None)


class LowercaseAttributeValueExpander(AttributeValueExpander):
  """Value expander that expands based on lower case object attribute names."""

  def _GetAttributeName(self, path):
    """Retrieves the attribute name to fetch given a path.

    Args:
      path (list[str]): object path, that contains the attribute names.

    Returns:
      str: attribute name.
    """
    return path[0].lower()


class DictValueExpander(ValueExpander):
  """Value expander that expands based on dictonary keys."""

  def _GetValue(self, obj, attr_name):
    """Retrieves the value of a specific object attribute.

    Args:
      obj (object): object to retrieve the value from.
      attr_name (str): name of the attribute to retrieve the value from.

    Returns:
      object: attribute value or None if attribute is not available.
    """
    return obj.get(attr_name, None)


# TODO: rename class.
class PlasoValueExpander(AttributeValueExpander):
  """An expander that gives values based on object attribute names."""

  def _GetAttributeName(self, path):
    """Retrieves the attribute name to fetch given a path.

    Args:
      path (list[str]): object path, that contains the attribute names.

    Returns:
      str: attribute name.
    """
    return path[0].lower()

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
