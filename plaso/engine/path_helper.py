# -*- coding: utf-8 -*-
"""The path helper."""

import os

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.engine import logger
from plaso.lib import definitions


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

    elif user_accounts:
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
    """Expands path segments with a users variable, such as %%users.homedir%%.

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
  def ExpandGlobStars(cls, path, path_separator):
    """Expands globstars "**" in a path.

    A globstar "**" will recursively match all files and zero or more
    directories and subdirectories.

    By default the maximum recursion depth is 10 subdirectories, a numeric
    values after the globstar, such as "**5", can be used to define the maximum
    recursion depth.

    Args:
      path (str): path to be expanded.
      path_separator (str): path segment separator.

    Returns:
      list[str]: String path expanded for each glob.
    """
    expanded_paths = []

    path_segments = path.split(path_separator)
    last_segment_index = len(path_segments) - 1
    for segment_index, path_segment in enumerate(path_segments):
      recursion_depth = None
      if path_segment.startswith('**'):
        if len(path_segment) == 2:
          recursion_depth = 10
        else:
          try:
            recursion_depth = int(path_segment[2:], 10)
          except (TypeError, ValueError):
            logger.warning((
                f'Globstar with suffix "{path_segment:s}" in path "{path:s}" '
                f'not supported.'))

      elif '**' in path_segment:
        logger.warning((
            f'Globstar with prefix "{path_segment:s}" in path "{path:s}" not '
            f'supported.'))

      if recursion_depth is not None:
        if recursion_depth <= 1 or recursion_depth > cls._RECURSIVE_GLOB_LIMIT:
          logger.warning((
              f'Globstar "{path_segment:s}" in path "{path:s}" exceed '
              f'recursion maximum recursion depth, limiting to: '
              f'{cls._RECURSIVE_GLOB_LIMIT:d}.'))
          recursion_depth = cls._RECURSIVE_GLOB_LIMIT

        next_segment_index = segment_index + 1
        for expanded_path_segment in [
            ['*'] * depth for depth in range(1, recursion_depth + 1)]:
          expanded_path_segments = list(path_segments[:segment_index])
          expanded_path_segments.extend(expanded_path_segment)
          if next_segment_index <= last_segment_index:
            expanded_path_segments.extend(path_segments[next_segment_index:])

          expanded_path = path_separator.join(expanded_path_segments)
          expanded_paths.append(expanded_path)

    return expanded_paths or [path]

  @classmethod
  def ExpandUsersVariablePath(cls, path, path_separator, user_accounts):
    """Expands a path with a users variable, such as %%users.homedir%%.

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
    path_segments = path.split('\\')
    path_segments = cls.ExpandWindowsPathSegments(
        path_segments, environment_variables)
    return '\\'.join(path_segments)

  @classmethod
  def ExpandWindowsPathSegments(cls, path_segments, environment_variables):
    """Expands a Windows path segments containing environment variables.

    Args:
      path_segments (list[str]): Windows path segments with environment
          variables.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.

    Returns:
      list[str]: expanded Windows path segments.
    """
    if environment_variables is None:
      environment_variables = []

    lookup_table = {}
    if environment_variables:
      for environment_variable in environment_variables:
        attribute_name = environment_variable.name.upper()
        attribute_value = environment_variable.value
        if not isinstance(attribute_value, str):
          continue

        lookup_table[attribute_name] = attribute_value

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

    return path_segments

  @classmethod
  def GetDisplayNameForPathSpec(cls, path_spec):
    """Retrieves the display name of a path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: human readable version of the path specification or None if no path
          specification was provided.
    """
    if not path_spec:
      return None

    relative_path = cls.GetRelativePathForPathSpec(path_spec)
    if not relative_path:
      return path_spec.type_indicator

    path_type_indicator = path_spec.type_indicator

    parent_path_spec = path_spec.parent
    if parent_path_spec:
      if path_spec.type_indicator == (
          dfvfs_definitions.TYPE_INDICATOR_COMPRESSED_STREAM):
        path_type_indicator = path_spec.compression_method.upper()
        parent_path_spec = parent_path_spec.parent

      elif path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_GZIP:
        parent_path_spec = parent_path_spec.parent

    display_name = ':'.join([path_type_indicator, relative_path])
    display_name = display_name.translate(
        definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)

    if parent_path_spec and parent_path_spec.type_indicator == (
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
      store_index = getattr(path_spec.parent, 'store_index', None)
      if store_index is not None:
        store_index += 1
        return f'VSS{store_index:d}:{display_name:s}'

    return display_name

  @classmethod
  def GetRelativePathForPathSpec(cls, path_spec):
    """Retrieves the relative path of a path specification.

    If a mount path is defined the path will be relative to the mount point,
    otherwise the path is relative to the root of the file system that is used
    by the path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

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
      location = ':'.join([location, data_stream])

    location = location.translate(
        definitions.NON_PRINTABLE_CHARACTER_TRANSLATION_TABLE)

    if path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_OS:
      return location

    return location

  @classmethod
  def GetPathSegmentSeparator(cls, path_spec):
    """Retrieves the path segment separator of path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: path segment separator.
    """
    if path_spec:
      if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_NTFS:
        return '\\'

      if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
        return os.path.sep

    return '/'

  @classmethod
  def GetWindowsSystemPath(cls, path, environment_variables):
    """Retrieves a Windows system path.

    Args:
      path (str): Windows path with environment variables.
      environment_variables (list[EnvironmentVariableArtifact]): environment
          variables.

    Returns:
      tuple[str, str]: Windows system path and filename.
    """
    path, _, filename = path.rpartition('\\')

    # If the path is just a filename assume the file is stored in:
    # "%SystemRoot%\System32".
    if not path:
      path = '%SystemRoot%\\System32'

    path = cls.ExpandWindowsPath(path, environment_variables)

    return path, filename
