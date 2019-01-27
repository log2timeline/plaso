# -*- coding: utf-8 -*-
"""The plist file object."""

from __future__ import unicode_literals

import biplist


class PlistFile(object):
  """Class that defines a plist file.

  Attributes:
    root_key (dict): the plist root key.
  """

  def __init__(self):
    """Initializes the plist file object."""
    super(PlistFile, self).__init__()
    self.root_key = None

  def GetValueByPath(self, path_segments):
    """Retrieves a plist value by path.

    Args:
      path_segments (list[str]): path segment strings relative to the root
          of the plist.

    Returns:
      object: The value of the key specified by the path or None.
    """
    key = self.root_key
    for path_segment in path_segments:
      if isinstance(key, dict):
        try:
          key = key[path_segment]
        except KeyError:
          return None

      elif isinstance(key, list):
        try:
          list_index = int(path_segment, 10)
        except ValueError:
          return None

        key = key[list_index]

      else:
        return None

      if not key:
        return None

    return key

  def Read(self, file_object):
    """Reads a plist from a file-like object.

    Args:
      file_object (dfvfs.FileIO): a file-like object containing plist data.

    Raises:
      IOError: if the plist file-like object cannot be read.
      OSError: if the plist file-like object cannot be read.
    """
    try:
      self.root_key = biplist.readPlist(file_object)

    except (
        biplist.NotBinaryPlistException,
        biplist.InvalidPlistException) as exception:
      raise IOError(exception)
