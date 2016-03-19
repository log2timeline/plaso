# -*- coding: utf-8 -*-
"""The plist file object."""

import binascii
import os
import plistlib

from binplist import binplist


class PlistFile(object):
  """Class that defines a plist file.

  Attributes:
    root_key: the plist root key (instance of plistlib._InternalDict).
  """

  def __init__(self):
    """Initializes the plist file object."""
    super(PlistFile, self).__init__()
    self.root_key = None

  def GetValueByPath(self, path_segments):
    """Retrieves a plist value by path.

    Args:
      path_segments: a list of path segments strings relative from the root
                     of the plist.

    Returns:
      The value of the key specified by the path or None.
    """
    key = self.root_key
    for path_segment in path_segments:
      # pylint: disable=protected-access
      if isinstance(key, (dict, plistlib._InternalDict)):
        key = key.get(path_segment)

      elif isinstance(key, list):
        try:
          list_index = int(path_segment, 10)
        except ValueError:
          return

        key = key[list_index]

      else:
        return

      if not key:
        return

    return key

  def Read(self, file_object):
    """Reads a plist from a file-like object.

    Args:
      file_object: the file-like object.

    Raises:
      IOError: if the plist file-like object cannot be read.
    """
    try:
      file_object.seek(0, os.SEEK_SET)
      # Note that binplist.readPlist does not seek to offset 0.
      self.root_key = binplist.readPlist(file_object)

    except (
        AttributeError, binascii.Error, binplist.FormatError, LookupError,
        OverflowError, ValueError) as exception:
      raise IOError(exception)
