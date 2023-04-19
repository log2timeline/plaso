# -*- coding: utf-8 -*-
"""Path filters.

Path filters are specified in filter files and are used during collection
to include or exclude file system paths.
"""

from dfvfs.helpers import file_system_searcher

from plaso.engine import logger
from plaso.engine import path_helper


class PathFilter(object):
  """Path filter.

  Attributes:
    description (str): description of the purpose of the filter or None if
        not set.
    filter_type (str): indicates if the filter should include or excludes
        paths during collection.
    path_separator (str): path segment separator.
    paths (list[str]): paths to filter.
  """

  FILTER_TYPE_EXCLUDE = 'exclude'
  FILTER_TYPE_INCLUDE = 'include'

  def __init__(
      self, filter_type, description=None, path_separator='/', paths=None):
    """Initializes a path filter.

    Args:
      filter_type (str): indicates if the filter should include or excludes
          paths during collection.
      description (Optional[str]): description of the purpose of the filter.
      path_separator (Optional[str]): path segment separator.
      paths (Optional[list[str]]): paths to filter.

    Raises:
      ValueError: if the filter type contains an unsupported value.
    """
    if filter_type not in (self.FILTER_TYPE_EXCLUDE, self.FILTER_TYPE_INCLUDE):
      raise ValueError('Unsupported filter type: {0!s}'.format(filter_type))

    super(PathFilter, self).__init__()
    self.description = description
    self.filter_type = filter_type
    self.path_separator = path_separator
    self.paths = paths or []


class PathCollectionFiltersHelper(object):
  """Path collection filters helper.

  Attributes:
    excluded_file_system_find_specs (list[dfvfs.FindSpec]): file system find
        specifications of paths to exclude from the collection.
    included_file_system_find_specs (list[dfvfs.FindSpec]): file system find
        specifications of paths to include in the collection.
  """

  def __init__(self):
    """Initializes a collection filters helper."""
    super(PathCollectionFiltersHelper, self).__init__()
    self.excluded_file_system_find_specs = []
    self.included_file_system_find_specs = []

  def BuildFindSpecs(self, path_filters, environment_variables=None):
    """Builds find specifications from path filters.

    Args:
      path_filters (list[PathFilter]): path filters.
      environment_variables (Optional[list[EnvironmentVariableArtifact]]):
          environment variables.
    """
    for path_filter in path_filters:
      for path in path_filter.paths:
        # Since paths are regular expression the path separator is escaped.
        if path_filter.path_separator == '\\':
          path_separator = '\\\\'
        else:
          path_separator = path_filter.path_separator

        expand_path = False
        path_segments = path.split(path_separator)
        for index, path_segment in enumerate(path_segments):
          if len(path_segment) <= 2:
            continue

          if path_segment[0] == '{' and path_segment[-1] == '}':
            # Rewrite legacy path expansion attributes, such as {systemroot}
            # into %SystemRoot%.
            path_segment = '%{0:s}%'.format(path_segment[1:-1])
            path_segments[index] = path_segment

          if path_segment[0] == '%' and path_segment[-1] == '%':
            expand_path = True

        if expand_path:
          path_segments = path_helper.PathHelper.ExpandWindowsPathSegments(
              path_segments, environment_variables)

        if path_segments[0] != '':
          logger.warning((
              'The path filter must be defined as an absolute path: '
              '{0:s}').format(path))
          continue

        # Strip the root path segment.
        path_segments.pop(0)

        if not path_segments[-1]:
          logger.warning(
              'Empty last path segment in path: {0:s}'.format(path))
          continue

        find_spec = file_system_searcher.FindSpec(
            case_sensitive=False, location_regex=path_segments)

        if path_filter.filter_type == PathFilter.FILTER_TYPE_EXCLUDE:
          self.excluded_file_system_find_specs.append(find_spec)

        elif path_filter.filter_type == PathFilter.FILTER_TYPE_INCLUDE:
          self.included_file_system_find_specs.append(find_spec)
