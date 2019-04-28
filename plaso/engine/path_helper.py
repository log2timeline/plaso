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

  _PATH_EXPANSIONS_PER_USERS_VARIABLE = {
      '%%users.appdata%%': [
          ['%%users.userprofile%%', 'AppData', 'Roaming'],
          ['%%users.userprofile%%', 'Application Data']],
      '%%users.localappdata%%': [
          ['%%users.userprofile%%', 'AppData', 'Local'],
          ['%%users.userprofile%%', 'Local Settings', 'Application Data']],
      '%%users.localappdata_low%%': [
          ['%%users.userprofile%%', 'AppData', 'LocalLow']],
      '%%users.temp%%': [
          ['%%users.localappdata%%', 'Temp']]}

  @classmethod
  def _ExpandUsersHomeDirectoryPathSegments(
      cls, path_segments, path_separator, user_accounts):
    """Expands a path to contain all users home or profile directories.

    Expands the artifacts path variable "%%users.homedir%%" or
    "%%users.userprofile%%".

    Args:
      path_segments (list[str]): path segments.
      path_separator (str): path segment separator.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[str]: paths returned for user accounts without a drive indicator.
    """
    if not path_segments:
      return []

    user_paths = []

    first_path_segment = path_segments[0].lower()
    if first_path_segment not in ('%%users.homedir%%', '%%users.userprofile%%'):
      if cls._IsWindowsDrivePathSegment(path_segments[0]):
        path_segments[0] = ''

      user_path = path_separator.join(path_segments)
      user_paths.append(user_path)

    else:
      for user_account in user_accounts:
        user_path_segments = user_account.GetUserDirectoryPathSegments()

        if not user_path_segments:
          continue

        if cls._IsWindowsDrivePathSegment(user_path_segments[0]):
          user_path_segments[0] = ''

        # Prevent concatenating two consecutive path segment separators.
        if not user_path_segments[-1]:
          user_path_segments.pop()

        user_path_segments.extend(path_segments[1:])

        user_path = path_separator.join(user_path_segments)
        user_paths.append(user_path)

    return user_paths

  @classmethod
  def _ExpandUsersVariablePathSegments(
      cls, path_segments, path_separator, user_accounts):
    """Expands path segments with a users variable, e.g. %%users.homedir%%.

    Args:
      path_segments (list[str]): path segments.
      path_separator (str): path segment separator.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[str]: paths for which the users variables have been expanded.
    """
    if not path_segments:
      return []

    path_segments_lower = [
        path_segment.lower() for path_segment in path_segments]

    if path_segments_lower[0] in ('%%users.homedir%%', '%%users.userprofile%%'):
      return cls._ExpandUsersHomeDirectoryPathSegments(
          path_segments, path_separator, user_accounts)

    path_expansions = cls._PATH_EXPANSIONS_PER_USERS_VARIABLE.get(
        path_segments[0], None)

    if path_expansions:
      expanded_paths = []

      for path_expansion in path_expansions:
        expanded_path_segments = list(path_expansion)
        expanded_path_segments.extend(path_segments[1:])

        paths = cls._ExpandUsersVariablePathSegments(
            expanded_path_segments, path_separator, user_accounts)
        expanded_paths.extend(paths)

      return expanded_paths

    if cls._IsWindowsDrivePathSegment(path_segments[0]):
      path_segments[0] = ''

    # TODO: add support for %%users.username%%
    path = path_separator.join(path_segments)
    return [path]

  @classmethod
  def _IsWindowsDrivePathSegment(cls, path_segment):
    """Determines if the path segment contains a Windows Drive indicator.

    A drive indicator can be a drive letter or %SystemDrive%.

    Args:
      path_segment (str): path segment.

    Returns:
      bool: True if the path segment contains a Windows Drive indicator.
    """
    if (len(path_segment) == 2 and path_segment[1] == ':' and
        path_segment[0].isalpha()):
      return True

    path_segment = path_segment.upper()
    return path_segment in ('%%ENVIRON_SYSTEMDRIVE%%', '%SYSTEMDRIVE%')

  @classmethod
  def AppendPathEntries(
      cls, path, path_separator, number_of_wildcards, skip_first):
    """Appends glob wildcards to a path.

    This function will append glob wildcards "*" to a path, returning paths
    with an additional glob wildcard up to the specified number. E.g. given
    the path "/tmp" and a number of 2 wildcards, this function will return
    "tmp/*", "tmp/*/*". When skip_first is true the path with the first
    wildcard is not returned as a result.

    Args:
      path (str): path to append glob wildcards to.
      path_separator (str): path segment separator.
      number_of_wildcards (int): number of glob wildcards to append.
      skip_first (bool): True if the the first path with glob wildcard should
          be skipped as a result.

    Returns:
      list[str]: paths with glob wildcards.
    """
    if path[-1] == path_separator:
      path = path[:-1]

    if skip_first:
      path = ''.join([path, path_separator, '*'])
      number_of_wildcards -= 1

    paths = []
    for _ in range(0, number_of_wildcards):
      path = ''.join([path, path_separator, '*'])
      paths.append(path)

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
    glob_regex = r'(.*)?{0:s}\*\*(\d{{1,2}})?({0:s})?$'.format(
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
  def ExpandUsersVariablePath(cls, path, path_separator, user_accounts):
    """Expands a path with a users variable, e.g. %%users.homedir%%.

    Args:
      path (str): path with users variable.
      path_separator (str): path segment separator.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list[str]: paths for which the users variables have been expanded.
    """
    path_segments = path.split(path_separator)
    return cls._ExpandUsersVariablePathSegments(
        path_segments, path_separator, user_accounts)

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
    # Make a copy of path_segments since this loop can change it.
    for index, path_segment in enumerate(list(path_segments)):
      if (len(path_segment) <= 2 or not path_segment.startswith('%') or
          not path_segment.endswith('%')):
        continue

      path_segment_upper_case = path_segment.upper()
      if path_segment_upper_case.startswith('%%ENVIRON_'):
        lookup_key = path_segment_upper_case[10:-2]
      else:
        lookup_key = path_segment_upper_case[1:-1]
      path_segment = lookup_table.get(lookup_key, path_segment)
      path_segment = path_segment.split('\\')

      expanded_path_segments = list(path_segments[:index])
      expanded_path_segments.extend(path_segment)
      expanded_path_segments.extend(path_segments[index + 1:])

      path_segments = expanded_path_segments

    if cls._IsWindowsDrivePathSegment(path_segments[0]):
      path_segments[0] = ''

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
