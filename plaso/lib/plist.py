# -*- coding: utf-8 -*-
"""The plist file object."""

import binascii
import os

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
      key: the plist key (instance of plistlib._InternalDict).
      path_segments: a list of path segments relative from the root
                     of the plist.

    Returns:
      The value of the key specified by the path.
    """
    key = self.root_key
    for path_segment in path_segments:
      key = key.get(path_segment)
      if not key:
        break
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
