# -*- coding: utf-8 -*-
"""The SHA-1 Hasher implementation"""

import hashlib

from plaso.hashers import interface
from plaso.hashers import manager


class SHA1Hasher(interface.BaseHasher):
  """This class provides SHA-1 hashing functionality."""

  NAME = u'sha1'
  DESCRIPTION = u'Calculates a SHA-1 digest hash over input data.'

  def __init__(self):
    """Initializes the SHA-1 hasher."""
    super(SHA1Hasher, self).__init__()
    self._sha1_context = hashlib.sha1()

  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data: a string of data with which to update the context of the hasher.
    """
    self._sha1_context.update(data)

  def GetStringDigest(self):
    """Returns the digest of the hash function expressed as a unicode string.

    Returns:
      A string hash digest calculated over the data blocks passed to
      Update(). The string will consist of printable Unicode characters.
    """
    return u'{0:s}'.format(self._sha1_context.hexdigest())

  def GetBinaryDigest(self):
    """Returns the digest of the hash function as a binary string.

    Returns:
      A binary string hash digest calculated over the data blocks passed to
      Update().
    """
    return self._sha1_context.digest()


manager.HashersManager.RegisterHasher(SHA1Hasher)
