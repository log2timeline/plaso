# -*- coding: utf-8 -*-
"""YAML-based filter file."""

import io
import yaml

from plaso.engine import path_filters
from plaso.lib import errors


class YAMLFilterFile(object):
  """YAML-based filter file.

  A YAML-based filter file contains one or more path filters.
  description: Include filter with Linux paths.
  type: include
  path_separator: '/'
  paths:
  - '/usr/bin'

  Where:
  * description, is an optional description of the purpose of the path filter;
  * type, defines the filter type, which can be "include" or "exclude";
  * path_separator, defines the path segment separator, which is "/" by default;
  * paths, defines regular expression of paths to filter on.

  Note that the regular expression need to be defined per path segment, for
  example to filter "/usr/bin/echo" and "/usr/sbin/echo" the following
  expression could be defined "/usr/(bin|sbin)/echo".

  Note that when the path segment separator is defined as "\\" it needs to be
  escaped as "\\\\", since "\\" is used by the regular expression as escape
  character.

  A path may contain path expansion attributes, for example:
  %{SystemRoot}\\\\System32
  """

  _SUPPORTED_KEYS = frozenset([
      'description',
      'path_separator',
      'paths',
      'type'])

  def _ReadFilterDefinition(self, filter_definition_values):
    """Reads a filter definition from a dictionary.

    Args:
      filter_definition_values (dict[str, object]): filter definition values.

    Returns:
      PathFilter: a path filter.

    Raises:
      ParseError: if the format of the filter definition is not set
          or incorrect.
    """
    if not filter_definition_values:
      raise errors.ParseError('Missing filter definition values.')

    different_keys = set(filter_definition_values) - self._SUPPORTED_KEYS
    if different_keys:
      different_keys = ', '.join(different_keys)
      raise errors.ParseError('Undefined keys: {0:s}'.format(different_keys))

    filter_type = filter_definition_values.get('type', None)
    if not filter_type:
      raise errors.ParseError('Invalid path filter definition missing type.')

    if filter_type not in (
        path_filters.PathFilter.FILTER_TYPE_EXCLUDE,
        path_filters.PathFilter.FILTER_TYPE_INCLUDE):
      raise errors.ParseError(
          'Invalid path filter definition unsupported type: {0!s}.'.format(
              filter_type))

    paths = filter_definition_values.get('paths', None)

    if not paths:
      raise errors.ParseError('Invalid path filter definition missing paths.')

    description = filter_definition_values.get('description', None)
    path_separator = filter_definition_values.get('path_separator', '/')

    return path_filters.PathFilter(
        filter_type, description=description, path_separator=path_separator,
        paths=paths)

  def _ReadFromFileObject(self, file_object):
    """Reads the path filters from a file-like object.

    Args:
      file_object (file): filter file-like object.

    Yields:
      PathFilter: path filter.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_definition in yaml_generator:
      yield self._ReadFilterDefinition(yaml_definition)

  def ReadFromFile(self, path):
    """Reads the path filters from the YAML-based filter file.

    Args:
      path (str): path to a filter file.

    Returns:
      list[PathFilter]: path filters.
    """
    with io.open(path, 'r', encoding='utf-8') as file_object:
      return list(self._ReadFromFileObject(file_object))
