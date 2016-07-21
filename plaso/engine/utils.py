# -*- coding: utf-8 -*-
"""Engine utility functions."""

import logging

from dfvfs.helpers import file_system_searcher

from plaso.lib import py2to3


def BuildFindSpecsFromFile(filter_file_path, path_attributes=None):
  """Returns a list of find specification from a filter file.

  A filter file path may contain paths that are attributes. A filter path
  attribute is defined as anything within a curly bracket, e.g.
  "\\System\\{my_attribute}\\Path\\Keyname". If the path attribute
  my_attribute is defined its value will be replaced with the attribute
  name, e.g. "\\System\\MyValue\\Path\\Keyname".

  If the path needs to have curly brackets in the path then they need
  to be escaped with another curly bracket, e.g.
  "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
  case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

  Args:
    filter_file_path (str): path to a file that contains find specifications.
    path_attributes (Optional[dict[str, str]]): path attributes e.g.
        {'SystemRoot': '\\Windows'}
  """
  find_specs = []

  filter_path_attributes = {}
  if path_attributes:
    for key, value in iter(path_attributes.items()):
      if not isinstance(value, py2to3.STRING_TYPES):
        continue

      if value.startswith(u'\\'):
        value = value.replace(u'\\', u'/')

      filter_path_attributes[key.lower()] = value

  with open(filter_file_path, 'rb') as file_object:
    for line in file_object:
      line = line.strip()
      if line.startswith(u'#'):
        continue

      if filter_path_attributes:
        try:
          line = line.format(**filter_path_attributes)
        except KeyError as exception:
          logging.error((
              u'Unable to expand filter path: {0:s} with error: '
              u'{1:s}').format(line, exception))
          continue

      if not line.startswith(u'/'):
        logging.warning((
            u'The filter string must be defined as an abolute path: '
            u'{0:s}').format(line))
        continue

      _, _, file_path = line.rstrip().rpartition(u'/')
      if not file_path:
        logging.warning(
            u'Unable to parse the filter string: {0:s}'.format(line))
        continue

      # Convert the filter paths into a list of path segments and strip
      # the root path segment.
      path_segments = line.split(u'/')
      path_segments.pop(0)

      find_specs.append(file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False))

  return find_specs
