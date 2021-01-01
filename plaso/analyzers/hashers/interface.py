# -*- coding: utf-8 -*-
"""The hasher interface."""

import abc


class BaseHasher(object):
  """Base class for objects that calculate hashes."""

  NAME = 'base_hasher'
  ATTRIBUTE_NAME = 'hash'
  DESCRIPTION = 'Calculates a digest hash over input data.'

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def GetStringDigest(self):
    """Retrieves the digest of the hash function expressed as a Unicode string.

    Returns:
      str: string hash digest calculated over the data blocks passed to
          Update(). The string consists of printable Unicode characters.
    """

  # pylint: disable=redundant-returns-doc
  @abc.abstractmethod
  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data (bytes): data with which to update the context of the hasher.
    """
