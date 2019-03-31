# -*- coding: utf-8 -*-
"""The entropy hasher implementation."""

from __future__ import unicode_literals

import codecs
import collections
import math

from plaso.analyzers.hashers import interface
from plaso.analyzers.hashers import manager


class EntropyHasher(interface.BaseHasher):
  """This class provides entropy hashing functionality."""

  NAME = 'entropy'
  DESCRIPTION = 'Calculates an entropy digest hash over input data.'

  def __init__(self):
    """Initializes the entropy hasher."""
    super(EntropyHasher, self).__init__()
    self._counter = collections.Counter()
    self._length = 0

  @classmethod
  def GetAttributeName(cls):
    """Determines the attribute name for the hash result."""
    return 'file_entropy'

  def GetBinaryDigest(self):
    """Returns the digest of the hash function as a binary string.

    Returns:
      bytes: binary string hash digest calculated over the data blocks passed to
          Update().
    """
    string_digest = self.GetStringDigest()
    binary_digest = codecs.encode(string_digest, 'utf-8')
    return binary_digest

  def GetStringDigest(self):
    """Returns the digest of the hash function expressed as a Unicode string.

    Returns:
      str: string hash digest calculated over the data blocks passed to
          Update(). The string consists of printable Unicode characters.
    """
    entropy = 0
    for byte_frequency in self._counter.values():
      byte_probability = byte_frequency / self._length
      entropy += - byte_probability * math.log2(byte_probability)
    return '{0:f}'.format(entropy)


  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data(bytes): block of data with which to update the context of the hasher.
    """
    self._counter.update(data)
    self._length += len(data)


manager.HashersManager.RegisterHasher(EntropyHasher)
