# -*- coding: utf-8 -*-
"""List of object filters."""

import logging
import os

import yaml

from plaso.filters import interface
from plaso.filters import manager
from plaso.lib import errors


class ObjectFilterList(interface.FilterObject):
  """A list of filters with addtional metadata."""

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
            u'Unable to load rule file with error: {0:s}'.format(exception))
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
      if u'filter' not in meta:
        raise errors.WrongPlugin(
            u'Entry inside {0:s} does not contain a filter statement.'.format(
                name))

      meta_filter = meta.get(u'filter')
      matcher = self._GetMatcher(meta_filter)
      if not matcher:
        raise errors.WrongPlugin(
            u'Filter entry [{0:s}] malformed for rule: <{1:s}>'.format(
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
          u'ObjectFilterList requires an YAML file to be passed on, '
          u'this filter string is not a file.'))

    yaml.add_constructor(
        u'!include', self._IncludeKeyword, Loader=yaml.loader.SafeLoader)
    results = None

    with open(filter_expression, 'rb') as file_object:
      try:
        results = yaml.safe_load(file_object)
      except (yaml.scanner.ScannerError, IOError) as exception:
        raise errors.WrongPlugin(
            u'Unable to parse YAML file with error: {0:s}.'.format(exception))

    self.filters = []
    results_type = type(results)
    if results_type is dict:
      self._ParseEntry(results)
    elif results_type is list:
      for result in results:
        if not isinstance(result, dict):
          raise errors.WrongPlugin(
              u'Wrong format of YAML file, entry not a dict ({0:s})'.format(
                  results_type))
        self._ParseEntry(result)
    else:
      raise errors.WrongPlugin(
          u'Wrong format of YAML file, entry not a dict ({0:s})'.format(
              results_type))
    self._filter_expression = filter_expression

  def Match(self, event_object):
    """Determines if the filter matches an event object.

    Args:
      event_object: an event object (instance of EventObject).

    Returns:
      A boolean value that indicates a match.
    """
    if not self.filters:
      return True

    for name, matcher, meta in self.filters:
      self._decision = matcher.Matches(event_object)
      if self._decision:
        meta_description = meta.get(u'description', u'N/A')
        meta_urls = meta.get(u'urls', [])
        self._reason = u'[{0:s}] {1:s} {2:s}'.format(
            name, meta_description, u' - '.join(meta_urls))
        return True

    return False


manager.FiltersManager.RegisterFilter(ObjectFilterList)
