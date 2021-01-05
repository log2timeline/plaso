# -*- coding: utf-8 -*-
"""The SHA-256 Hasher implementation"""

import hashlib

from plaso.analyzers.hashers import interface
from plaso.analyzers.hashers import manager


class SHA256Hasher(interface.BaseHasher):
  """This class provides SHA-256 hashing functionality."""

  NAME = 'sha256'
  ATTRIBUTE_NAME = 'sha256_hash'
  DESCRIPTION = 'Calculates a SHA-256 digest hash over input data.'

  def __init__(self):
    """Initializes the SHA-256 hasher."""
    super(SHA256Hasher, self).__init__()
    self._sha256_context = hashlib.sha256()

  def GetStringDigest(self):
    """Returns the digest of the hash function expressed as a Unicode string.

    Returns:
      str: string hash digest calculated over the data blocks passed to
          Update(). The string consists of printable Unicode characters.
    """
    return '{0:s}'.format(self._sha256_context.hexdigest())

  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data(bytes): block of data with which to update the context of the hasher.
    """
    self._sha256_context.update(data)


manager.HashersManager.RegisterHasher(SHA256Hasher)
