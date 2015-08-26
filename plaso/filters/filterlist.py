# -*- coding: utf-8 -*-
"""List of object filters."""

import logging
import os
import yaml

from plaso.filters import interface
from plaso.lib import errors
from plaso.lib import pfilter


# TODO: This file requires a cleanup to confirm with project style etc.

def IncludeKeyword(loader, node):
  """A constructor for the include keyword in YAML.

  Args:
    loader: 
    node:
  """
  filename = loader.construct_scalar(node)
  if os.path.isfile(filename):
    with open(filename, 'rb') as file_object:
      try:
        data = yaml.safe_load(file_object)
      except yaml.ParserError as exception:
        logging.error(u'Unable to load rule file with error: {0:s}'.format(
            exception))
        return None
  return data


class ObjectFilterList(interface.FilterObject):
  """A list of filters with addtional metadata."""

  def CompileFilter(self, filter_string):
    """Compile a set of ObjectFilters defined in an YAML file.

    Args:
      filter_string: YAML string that defines the object filters.

    Raises:
      WrongPlugin: if the filter cannot be compiled.
    """
    if not os.path.isfile(filter_string):
      raise errors.WrongPlugin((
          u'ObjectFilterList requires an YAML file to be passed on, this filter '
          u'string is not a file.'))

    yaml.add_constructor(
        u'!include', IncludeKeyword, Loader=yaml.loader.SafeLoader)
    results = None

    with open(filter_string, 'rb') as file_object:
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
        if type(result) is not dict:
          raise errors.WrongPlugin(
              u'Wrong format of YAML file, entry not a dict ({0:s})'.format(
                  results_type))
        self._ParseEntry(result)
    else:
      raise errors.WrongPlugin(
          u'Wrong format of YAML file, entry not a dict ({0:s})'.format(
              results_type))
    self._filter_expression = filter_string

  def _ParseEntry(self, entry):
    """Parse a single YAML filter entry.

    Args:
      entry: the entry to parse.
    """
    # A single file with a list of filters to parse.
    for name, meta in entry.items():
      if u'filter' not in meta:
        raise errors.WrongPlugin(
            u'Entry inside {0:s} does not contain a filter statement.'.format(
                name))

      filter_meta = meta.get(u'filter')
      matcher = pfilter.GetMatcher(filter_meta, True)
      if not matcher:
        raise errors.WrongPlugin(
            u'Filter entry [{0:s}] malformed for rule: <{1:s}>'.format(
                filter_meta, name))

      self.filters.append((name, matcher, meta))

  def Match(self, event_object):
    """Determine if the filter matches an event object.

    Args:
      event_objetc: an event object (instance of EventObject).

    Returns:
      True if the filter matched None otherwise.
    """
    if not self.filters:
      return True

    for name, matcher, meta in self.filters:
      self._decision = matcher.Matches(event_object)
      if self._decision:
        self._reason = u'[{0:s}] {1:s} {2:s}'.format(
            name, meta.get(u'description', u'N/A'),
            u' - '.join(meta.get(u'urls', [])))
        return True

    return
