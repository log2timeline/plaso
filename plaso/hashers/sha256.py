# -*- coding: utf-8 -*-
"""The SHA-256 Hasher implementation"""

import hashlib

from plaso.hashers import interface
from plaso.hashers import manager


class SHA256Hasher(interface.BaseHasher):
  """This class provides SHA-256 hashing functionality."""

  NAME = u'sha256'
  DESCRIPTION = u'Calculates a SHA-256 digest hash over input data.'

  def __init__(self):
    """Initializes the SHA-256 hasher."""
    super(SHA256Hasher, self).__init__()
    self._sha256_context = hashlib.sha256()

  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data: a string of data with which to update the context of the hasher.
    """
    self._sha256_context.update(data)

  def GetStringDigest(self):
    """Returns the digest of the hash function expressed as a unicode string.

    Returns:
      A string hash digest calculated over the data blocks passed to
      Update(). The string will consist of printable Unicode characters.
    """
    return unicode(self._sha256_context.hexdigest())

  def GetBinaryDigest(self):
    """Returns the digest of the hash function as a binary string.

    Returns:
      A binary string hash digest calculated over the data blocks passed to
      Update().
    """
    return self._sha256_context.digest()


manager.HashersManager.RegisterHasher(SHA256Hasher)
