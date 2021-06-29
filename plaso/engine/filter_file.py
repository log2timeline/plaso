# -*- coding: utf-8 -*-
"""Filter file."""

import io

from plaso.engine import path_filters


class FilterFile(object):
  """Filter file.

  A filter file contains one or more path filters.

  A path filter may contain path expansion attributes. Such an attribute
  is defined as anything within a curly bracket, for example
  "\\System\\{my_attribute}\\Path\\Keyname". If the attribute "my_attribute"
  is defined its runtime value will be replaced with placeholder in the path
  filter such as "\\System\\MyValue\\Path\\Keyname".

  If the path filter needs to have curly brackets in the path then these need
  to be escaped with another curly bracket, for example
  "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName", where
  "{{123-AF25-E523}}" will be replaced with "{123-AF25-E523}" at runtime.
  """

  def _ReadFromFileObject(self, file_object):
    """Reads the path filters from the filter file-like object.

    Args:
      file_object (file): filter file-like object.

    Yields:
      PathFilter: path filter.
    """
    paths = []
    for line in file_object:
      line = line.strip()
      if line and not line.startswith('#'):
        paths.append(line)

    yield path_filters.PathFilter(
        path_filters.PathFilter.FILTER_TYPE_INCLUDE, paths=paths)

  def ReadFromFile(self, path):
    """Reads the path filters from the filter file.

    Args:
      path (str): path to a filter file.

    Returns:
      list[PathFilter]: path filters.
    """
    with io.open(path, 'r', encoding='utf-8') as file_object:
      return list(self._ReadFromFileObject(file_object))
