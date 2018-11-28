# -*- coding: utf-8 -*-
"""The path helper."""

from __future__ import unicode_literals

import re

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.engine import logger
from plaso.lib import py2to3


class PathHelper(object):
  """Class that implements the path helper."""

  _RECURSIVE_GLOB_LIMIT = 10

  @classmethod
  def AppendPathEntries(cls, path, path_separator, count, skip_first):
    """Appends wildcard entries to end of path.

    Will append wildcard * to given path building a list of strings for "count"
    iterations, skipping the first directory if skip_first is true.

    Args:
      path (str): Path to append wildcards to.
      path_separator (str): path segment separator.
      count (int): Number of entries to be appended.
      skip_first (bool): Whether or not to skip first entry to append.

    Returns:
      list[str]: Paths that were expanded from the path with wildcards.
    """
    paths = []
    replacement = '{0:s}*'.format(path_separator)

    iteration = 0
    while iteration < count:
      if skip_first and iteration == 0:
        path += replacement
      else:
        path += replacement
        paths.append(path)
      iteration += 1

    return paths

  @classmethod
  def ExpandRecursiveGlobs(cls, path, path_separator):
    """Expands recursive like globs present in an artifact path.

    If a path ends in '**', with up to two optional digits such as '**10',
    the '**' will recursively match all files and zero or more directories
    from the specified path. The optional digits indicate the recursion depth.
    By default recursion depth is 10 directories.

    If the glob is followed by the specified path segment separator, only
    directories and subdirectories will be matched.

    Args:
      path (str): path to be expanded.
      path_separator (str): path segment separator.

    Returns:
      list[str]: String path expanded for each glob.
    """
    glob_regex = r'(.*)?{0}\*\*(\d{{1,2}})?({0})?$'.format(
        re.escape(path_separator))

    match = re.search(glob_regex, path)
    if not match:
      return [path]

    skip_first = False
    if match.group(3):
      skip_first = True
    if match.group(2):
      iterations = int(match.group(2))
    else:
      iterations = cls._RECURSIVE_GLOB_LIMIT
      logger.warning((
          'Path "{0:s}" contains fully recursive glob, limiting to 10 '
          'levels').format(path))

    return cls.AppendPathEntries(
        match.group(1), path_separator, iterations, skip_first)

  @classmethod
  def ExpandUsersHomeDirectoryPath(cls, path, user_accounts):
    """Expands a path to contain all users home or profile directories.

    Expands the GRR artifacts path variable "%%users.homedir%%".

    Args:
      path (str): Windows path with environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[str]: paths returned for user accounts without a drive letter.
    """
    path_upper_case = path.upper()
    if not path_upper_case.startswith('%%USERS.HOMEDIR%%'):
      user_paths = [path]
    else:
      regex = re.compile(re.escape('%%users.homedir%%'))

      user_paths = []
      for user_account in user_accounts:
        user_path = regex.sub(user_account.user_directory, path, re.IGNORECASE)
        user_paths.append(user_path)

    # Remove the drive letter, if it exists.
    for path_index, user_path in enumerate(user_paths):
      if len(user_path) > 2 and user_path[1] == ':':
        _, _, user_path = user_path.rpartition(':')
        user_paths[path_index] = user_path

    return user_paths

  @classmethod
  def ExpandWindowsPath(cls, path, environment_variables):
    """Expands a Windows path containing environment variables.

    Args:
      path (str): Windows path with environment variables.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.

    Returns:
      str: expanded Windows path.
    """
    # TODO: Add support for items such as %%users.localappdata%%

    if environment_variables is None:
      environment_variables = []

    lookup_table = {}
    if environment_variables:
      for environment_variable in environment_variables:
        attribute_name = environment_variable.name.upper()
        attribute_value = environment_variable.value
        if not isinstance(attribute_value, py2to3.STRING_TYPES):
          continue

        lookup_table[attribute_name] = attribute_value

    path_segments = path.split('\\')
    for index, path_segment in enumerate(path_segments):
      if (len(path_segment) <= 2 or not path_segment.startswith('%') or
          not path_segment.endswith('%')):
        continue

      check_for_drive_letter = False
      path_segment_upper_case = path_segment.upper()
      if path_segment_upper_case.startswith('%%ENVIRON_'):
        lookup_key = path_segment_upper_case[10:-2]
        check_for_drive_letter = True
      else:
        lookup_key = path_segment_upper_case[1:-1]
      path_segments[index] = lookup_table.get(lookup_key, path_segment)

      if check_for_drive_letter:
        # Remove the drive letter.
        if len(path_segments[index]) >= 2 and path_segments[index][1] == ':':
          _, _, path_segments[index] = path_segments[index].rpartition(':')

    return '\\'.join(path_segments)

  @classmethod
  def GetDisplayNameForPathSpec(
      cls, path_spec, mount_path=None, text_prepend=None):
    """Retrieves the display name of a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      mount_path (Optional[str]): path where the file system that is used
          by the path specification is mounted, such as "/mnt/image". The
          mount path will be stripped from the absolute path defined by
          the path specification.
      text_prepend (Optional[str]): text to prepend.

    Returns:
      str: human readable version of the path specification or None.
    """
    if not path_spec:
      return None

    relative_path = cls.GetRelativePathForPathSpec(
        path_spec, mount_path=mount_path)
    if not relative_path:
      return path_spec.type_indicator

    if text_prepend:
      relative_path = '{0:s}{1:s}'.format(text_prepend, relative_path)

    parent_path_spec = path_spec.parent
    if parent_path_spec and path_spec.type_indicator in (
        dfvfs_definitions.TYPE_INDICATOR_BZIP2,
        dfvfs_definitions.TYPE_INDICATOR_GZIP):
      parent_path_spec = parent_path_spec.parent

    if parent_path_spec and parent_path_spec.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
      store_index = getattr(path_spec.parent, 'store_index', None)
      if store_index is not None:
        return 'VSS{0:d}:{1:s}:{2:s}'.format(
            store_index + 1, path_spec.type_indicator, relative_path)

    return '{0:s}:{1:s}'.format(path_spec.type_indicator, relative_path)

  @classmethod
  def GetRelativePathForPathSpec(cls, path_spec, mount_path=None):
    """Retrieves the relative path of a path specification.

    If a mount path is defined the path will be relative to the mount point,
    otherwise the path is relative to the root of the file system that is used
    by the path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      mount_path (Optional[str]): path where the file system that is used
          by the path specification is mounted, such as "/mnt/image". The
          mount path will be stripped from the absolute path defined by
          the path specification.

    Returns:
      str: relative path or None.
    """
    if not path_spec:
      return None

    # TODO: Solve this differently, quite possibly inside dfVFS using mount
    # path spec.
    location = getattr(path_spec, 'location', None)
    if not location and path_spec.HasParent():
      location = getattr(path_spec.parent, 'location', None)

    if not location:
      return None

    data_stream = getattr(path_spec, 'data_stream', None)
    if data_stream:
      location = '{0:s}:{1:s}'.format(location, data_stream)

    if path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_OS:
      return location

    # If we are parsing a mount point we don't want to include the full
    # path to file's location here, we are only interested in the path
    # relative to the mount point.
    if mount_path and location.startswith(mount_path):
      location = location[len(mount_path):]

    return location
