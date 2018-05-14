# -*- coding: utf-8 -*-
"""The path helper."""

from __future__ import unicode_literals

import re

from dfvfs.lib import definitions as dfvfs_definitions

from plaso.lib import py2to3


class PathHelper(object):
  """Class that implements the path helper."""

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
    #TODO: Add support for items such as %%users.localappdata%%

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
      if path_segment.upper().startswith('%%ENVIRON_'):
        lookup_key = path_segment.upper()[10:-2]
        check_for_drive_letter = True
      else:
        lookup_key = path_segment.upper()[1:-1]
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
    if parent_path_spec and path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_BZIP2,
        dfvfs_definitions.TYPE_INDICATOR_GZIP]:
      parent_path_spec = parent_path_spec.parent

    if parent_path_spec and parent_path_spec.type_indicator in [
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW]:
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

  @classmethod
  def ExpandUserHomeDirPath(cls, path, user_accounts):
    """Expands a Windows path to contain all user home directories.

    Args:
      path (str): Windows path with environment variables.
      user_accounts (list[UserAccountArtifact]): user accounts.

    Returns:
      list [str]: paths returned for user accounts.
    """

    user_paths = []
    if path.upper().startswith('%%USERS.HOMEDIR%%'):
      regex = re.compile(re.escape('%%users.homedir%%'))
      for user_account in user_accounts:
        new_path = regex.sub(user_account.user_directory, path)
        user_paths.append(new_path)
    else:
      user_paths = [path]

    return user_paths
