# -*- coding: utf-8 -*-
import os
import yaml
import logging

from plaso.lib import errors
from plaso.lib import filter_interface
from plaso.lib import pfilter

# TODO: This file requires a cleanup to confirm with project style etc..

def IncludeKeyword(loader, node):
  """A constructor for the include keyword in YAML."""
  filename = loader.construct_scalar(node)
  if os.path.isfile(filename):
    with open(filename, 'rb') as fh:
      try:
        data = yaml.safe_load(fh)
      except yaml.ParserError as exception:
        logging.error(u'Unable to load rule file with error: {0:s}'.format(
            exception))
        return None
  return data


class ObjectFilterList(filter_interface.FilterObject):
  """A series of Pfilter filters along with metadata."""

  def CompileFilter(self, filter_string):
    """Compile a set of ObjectFilters defined in an YAML file."""
    if not os.path.isfile(filter_string):
      raise errors.WrongPlugin((
          'ObjectFilterList requires an YAML file to be passed on, this filter '
          'string is not a file.'))

    yaml.add_constructor('!include', IncludeKeyword,
                         Loader=yaml.loader.SafeLoader)
    results = None

    with open(filter_string, 'rb') as fh:
      try:
        results = yaml.safe_load(fh)
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
              u'Wrong format of YAML file, entry not a dict ({})'.format(
                  results_type))
        self._ParseEntry(result)
    else:
      raise errors.WrongPlugin(
          u'Wrong format of YAML file, entry not a dict ({})'.format(
              results_type))

  def _ParseEntry(self, entry):
    """Parse a single YAML filter entry."""
    # A single file with a list of filters to parse.
    for name, meta in entry.items():
      if 'filter' not in meta:
        raise errors.WrongPlugin(
            u'Entry inside {} does not contain a filter statement.'.format(
                name))

      matcher = pfilter.GetMatcher(meta.get('filter'), True)
      if not matcher:
        raise errors.WrongPlugin(
            u'Filter entry [{0:s}] malformed for rule: <{1:s}>'.format(
                meta.get('filter'), name))

      self.filters.append((name, matcher, meta))

  def Match(self, event_object):
    """Evaluate an EventObject against a pfilter."""
    if not self.filters:
      return True

    for name, matcher, meta in self.filters:
      self._decision = matcher.Matches(event_object)
      if self._decision:
        self._reason = u'[{}] {} {}'.format(
            name, meta.get('description', 'N/A'), u' - '.join(
                meta.get('urls', [])))
        return True

    return
