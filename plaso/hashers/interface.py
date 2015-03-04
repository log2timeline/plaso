# -*- coding: utf-8 -*-
"""This file contains a class to provide a hashing framework to Plaso.

This class contains a base framework class for parsing files.
"""

import abc


class BaseHasher(object):
  """Class that provides the interface for hashing functionality."""

  NAME = u'base_hasher'
  DESCRIPTION = u''

  @abc.abstractmethod
  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data: a string of data with which to update the context of the hasher.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def GetBinaryDigest(self):
    """Retrieves the digest of the hash function as a binary string.

    Returns:
      A binary string hash digest calculated over the data blocks passed to
      Update().
    """
    raise NotImplementedError

  @abc.abstractmethod
  def GetStringDigest(self):
    """Retrieves the digest of the hash function expressed as a unicode string.

    Returns:
      A string hash digest calculated over the data blocks passed to
      Update(). The string will consist of printable Unicode characters.
    """
    raise NotImplementedError
