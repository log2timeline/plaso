#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the hasher manager."""

import unittest

from plaso.analyzers.hashers import interface
from plaso.analyzers.hashers import manager

from tests import test_lib as shared_test_lib


class TestHasher(interface.BaseHasher):
  """Test hasher."""

  NAME = 'testhash'
  ATTRIBUTE_NAME = 'testhash_hash'

  def GetStringDigest(self):
    """Retrieves the digest of the hash function expressed as a Unicode string.

    Returns:
      str: string hash digest calculated over the data blocks passed to
          Update(). The string will consist of printable Unicode characters.
    """
    # Chosen by fair dice roll. Guaranteed to be random.
    # Compliant with RFC 1149.5. See http://xkcd.com/221/.
    return '4'

  # pylint: disable=unused-argument
  def Update(self, data):
    """Updates the current state of the hasher with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data (bytes): data with which to update the context of the hasher.
    """
    return


class HashersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the hashers manager."""

  # pylint: disable=protected-access

  def testHasherRegistration(self):
    """Tests the registration and deregistration of hashers."""
    number_of_parsers = len(manager.HashersManager._hasher_classes)
    manager.HashersManager.RegisterHasher(TestHasher)
    self.assertEqual(
        number_of_parsers + 1, len(manager.HashersManager._hasher_classes))

    with self.assertRaises(KeyError):
      manager.HashersManager.RegisterHasher(TestHasher)

    manager.HashersManager.DeregisterHasher(TestHasher)

    self.assertEqual(
        number_of_parsers, len(manager.HashersManager._hasher_classes))

  def testGetHashersInformation(self):
    """Tests the GetHashersInformation function."""
    hashers_information = manager.HashersManager.GetHashersInformation()

    self.assertGreaterEqual(len(hashers_information), 3)

    available_hasher_names = [name for name, _ in hashers_information]
    self.assertIn('sha1', available_hasher_names)
    self.assertIn('sha256', available_hasher_names)

  def testGetHasherNamesFromString(self):
    """Tests the GetHasherNamesFromString method."""
    test_strings = 'md5,sha256,testhash'
    manager.HashersManager.RegisterHasher(TestHasher)
    names = manager.HashersManager.GetHasherNamesFromString(test_strings)
    self.assertEqual(3, len(names))
    manager.HashersManager.DeregisterHasher(TestHasher)
    names = manager.HashersManager.GetHasherNamesFromString(test_strings)
    self.assertEqual(2, len(names))
    names = manager.HashersManager.GetHasherNamesFromString('all')
    self.assertEqual(len(names), len(manager.HashersManager._hasher_classes))

  def testGetHasher(self):
    """Tests the GetHasher function."""
    hasher_object = manager.HashersManager.GetHasher('md5')
    self.assertIsNotNone(hasher_object)
    self.assertEqual(hasher_object.NAME, 'md5')

    hasher_object = manager.HashersManager.GetHasher('sha1')
    self.assertIsNotNone(hasher_object)
    self.assertEqual(hasher_object.NAME, 'sha1')

    with self.assertRaises(KeyError):
      manager.HashersManager.GetHasher('bogus')

  def testGetHashers(self):
    """Tests the GetHashers and GetHasherNames functions."""
    hasher_names = manager.HashersManager.GetHasherNames()
    hashers = manager.HashersManager.GetHashers(hasher_names)
    self.assertEqual(len(hasher_names), len(hashers))
    for hasher in hashers:
      self.assertIsInstance(hasher, interface.BaseHasher)


if __name__ == '__main__':
  unittest.main()
