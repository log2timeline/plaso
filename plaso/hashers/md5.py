# -*- coding: utf-8 -*-
"""The MD5 hasher implementation."""

import hashlib

from plaso.hashers import interface
from plaso.hashers import manager


class MD5Hasher(interface.BaseHasher):
  """This class provides MD5 hashing functionality."""

  NAME = u'md5'
  DESCRIPTION = u'Calculates an MD5 digest hash over input data.'

  def __init__(self):
    """Initializes the MD5 hasher."""
    super(MD5Hasher, self).__init__()
    self._md5_context = hashlib.md5()

  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data: a string of data with which to update the context of the hasher.
    """
    self._md5_context.update(data)

  def GetStringDigest(self):
    """Returns the digest of the hash function expressed as a Unicode string.

    Returns:
      A string hash digest calculated over the data blocks passed to
      Update(). The string will consist of printable Unicode characters.
    """
    return u'{0:s}'.format(self._md5_context.hexdigest())

  def GetBinaryDigest(self):
    """Returns the digest of the hash function as a binary string.

    Returns:
      A binary string hash digest calculated over the data blocks passed to
      Update().
    """
    return self._md5_context.digest()


manager.HashersManager.RegisterHasher(MD5Hasher)
