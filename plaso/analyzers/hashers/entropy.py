# -*- coding: utf-8 -*-
"""The entropy calculation implementation."""

import collections
import math

from plaso.analyzers.hashers import interface
from plaso.analyzers.hashers import manager


class EntropyHasher(interface.BaseHasher):
  """Calculates the byte entropy of input files."""

  NAME = 'entropy'
  ATTRIBUTE_NAME = 'file_entropy'
  DESCRIPTION = 'Calculates the byte entropy of input data.'

  def __init__(self):
    """Initializes the entropy hasher."""
    super(EntropyHasher, self).__init__()
    self._byte_frequency_counter = collections.Counter()
    self._file_length = 0

  def GetStringDigest(self):
    """Calculates the byte entropy value.

    Byte entropy is a value between 0.0 and 8.0, and is returned as a string
    to match the Plaso analyzer and storage APIs.

    Returns:
      str: byte entropy formatted as a floating point number with 6 decimal
          places calculated over the data blocks passed to Update().
    """
    if self._file_length == 0:
      return '0.000000'

    entropy = 0.0
    for byte_frequency in self._byte_frequency_counter.values():
      byte_probability = byte_frequency / self._file_length
      if byte_probability:
        entropy += - byte_probability * math.log(byte_probability, 2)
    return '{0:.6f}'.format(entropy)

  def Update(self, data):
    """Updates the state of the entropy calculator with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data(bytes): block of data with which to update the context of the entropy
          calculator.
    """
    # The call to update() determines the number of occurrences of a byte value
    # within data.
    self._byte_frequency_counter.update(data)
    self._file_length += len(data)


manager.HashersManager.RegisterHasher(EntropyHasher)
