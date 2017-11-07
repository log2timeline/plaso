# -*- coding: utf-8 -*-
"""List of object-filters."""

from __future__ import unicode_literals

import logging
import os

import yaml

from plaso.filters import interface
from plaso.filters import manager
from plaso.lib import errors


class ObjectFilterList(interface.FilterObject):
  """A list of object-filters with additional metadata."""

  def __init__(self):
    """Initializes an object-filter list object."""
    super(ObjectFilterList, self).__init__()
    self.filters = None

  def _IncludeKeyword(self, loader, node):
    """Callback for YAML add_constructor.

    The YAML constructor is a function that converts a YAML node to a native
    Python object. A YAML constructor accepts an instance of Loader and a node
    and returns a Python object. For more information see:
    http://pyyaml.org/wiki/PyYAMLDocumentation

    Args:
      loader: the YAML loader object (instance of yaml.Loader).
      node: a YAML node (instance of yaml.TODO).

    Returns:
      A Python object or None.
    """
    filename = loader.construct_scalar(node)
    if not os.path.isfile(filename):
      return

    with open(filename, 'rb') as file_object:
      try:
        return yaml.safe_load(file_object)

      except yaml.ParserError as exception:
        logging.error(
            'Unable to load rule file with error: {0!s}'.format(exception))
        return

  def _ParseEntry(self, entry):
    """Parses a single filter entry.

    Args:
      entry: YAML string that defines a single object filter entry.

    Raises:
      WrongPlugin: if the entry cannot be parsed.
    """
    # A single file with a list of filters to parse.
    for name, meta in entry.items():
      if 'filter' not in meta:
        raise errors.WrongPlugin(
            'Entry inside {0:s} does not contain a filter statement.'.format(
                name))

      meta_filter = meta.get('filter')
      matcher = self._GetMatcher(meta_filter)
      if not matcher:
        raise errors.WrongPlugin(
            'Filter entry [{0:s}] malformed for rule: <{1:s}>'.format(
                meta_filter, name))

      self.filters.append((name, matcher, meta))

  def CompileFilter(self, filter_expression):
    """Compiles the filter expression.

    The filter expression contains the name of a YAML file.

    Args:
      filter_expression: string that contains the filter expression.

    Raises:
      WrongPlugin: if the filter could not be compiled.
    """
    if not os.path.isfile(filter_expression):
      raise errors.WrongPlugin((
          'ObjectFilterList requires an YAML file to be passed on, '
          'this filter string is not a file.'))

    yaml.add_constructor(
        '!include', self._IncludeKeyword, Loader=yaml.loader.SafeLoader)
    results = None

    with open(filter_expression, 'rb') as file_object:
      try:
        results = yaml.safe_load(file_object)
      except (yaml.scanner.ScannerError, IOError) as exception:
        raise errors.WrongPlugin(
            'Unable to parse YAML file with error: {0!s}.'.format(exception))

    self.filters = []
    results_type = type(results)
    if results_type is dict:
      self._ParseEntry(results)
    elif results_type is list:
      for result in results:
        if not isinstance(result, dict):
          raise errors.WrongPlugin(
              'Wrong format of YAML file, entry not a dict ({0:s})'.format(
                  results_type))
        self._ParseEntry(result)
    else:
      raise errors.WrongPlugin(
          'Wrong format of YAML file, entry not a dict ({0:s})'.format(
              results_type))
    self._filter_expression = filter_expression

  def Match(self, event_object):
    """Determines if an event object matches the filter.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A boolean value that indicates a match.
    """
    if not self.filters:
      return True

    for _, matcher, _ in self.filters:
      if matcher.Matches(event_object):
        return True

    return False


manager.FiltersManager.RegisterFilter(ObjectFilterList)
