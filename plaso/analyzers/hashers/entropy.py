# -*- coding: utf-8 -*-
"""The entropy calculation implementation."""

from __future__ import unicode_literals

import collections
import math

from plaso.analyzers.hashers import interface
from plaso.analyzers.hashers import manager


class EntropyHasher(interface.BaseHasher):
  """Calculates the byte entropy of input files."""

  NAME = 'entropy'
  DESCRIPTION = 'Calculates the entropy of input data.'

  def __init__(self):
    """Initializes the entropy hasher."""
    super(EntropyHasher, self).__init__()
    self._counter = collections.Counter()
    self._length = 0

  @classmethod
  def GetAttributeName(cls):
    """The attribute name for the result."""
    return 'file_entropy'

  def GetStringDigest(self):
    """Calculates a unicode string containing the entropy value.

    Byte entropy is a value between 0.0 and 8.0, and is returned as a string
    to match the Plaso analyzer and storage APIs.

    Returns:
      str: byte entropy calculated over the data blocks passed to
          Update().
    """
    if self._length == 0:
      return '0.0'

    entropy = 0
    for byte_frequency in self._counter.values():
      byte_probability = byte_frequency / self._length
      if byte_probability:
        entropy += - byte_probability * math.log(byte_probability, 2)
    return '{0:f}'.format(entropy)

  def Update(self, data):
    """Updates the state of the entropy calculator with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data(bytes): block of data with which to update the context of the entropy
          calculator.
    """
    self._counter.update(data)
    self._length += len(data)


manager.HashersManager.RegisterHasher(EntropyHasher)
