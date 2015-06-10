# -*- coding: utf-8 -*-
"""Tests for the hasher manager."""

import unittest

from plaso.hashers import interface
from plaso.hashers import manager


class TestHasher(interface.BaseHasher):
  """A dummy test hasher."""

  NAME = u'testhash'

  def Update(self, data):
    return

  def GetBinaryDigest(self):
    # Chosen by fair dice roll. Guaranteed to be random.
    # Compliant with RFC 1149.4. See http://xkcd.com/221/.
    return '4'

  def GetStringDigest(self):
    # Chosen by fair dice roll. Guaranteed to be random.
    # Compliant with RFC 1149.4. See http://xkcd.com/221/.
    return u'4'


class HashersManagerTest(unittest.TestCase):
  """Tests for the hashers manager."""

  def testHasherRegistration(self):
    """Tests the registration and deregistration of hashers."""
    # pylint: disable=protected-access
    number_of_parsers = len(manager.HashersManager._hasher_classes)
    manager.HashersManager.RegisterHasher(TestHasher)
    self.assertEqual(
        number_of_parsers + 1, len(manager.HashersManager._hasher_classes))

    with self.assertRaises(KeyError):
      manager.HashersManager.RegisterHasher(TestHasher)

    manager.HashersManager.DeregisterHasher(TestHasher)

    self.assertEqual(
        number_of_parsers, len(manager.HashersManager._hasher_classes))

  def testGetHasherNamesFromString(self):
    """Tests the GetHasherNamesFromString method."""
    test_strings = u'md5,sha256,testhash'
    manager.HashersManager.RegisterHasher(TestHasher)
    names = manager.HashersManager.GetHasherNamesFromString(test_strings)
    self.assertEqual(3, len(names))
    manager.HashersManager.DeregisterHasher(TestHasher)
    names = manager.HashersManager.GetHasherNamesFromString(test_strings)
    self.assertEqual(2, len(names))
    names = manager.HashersManager.GetHasherNamesFromString(u'all')
    self.assertEqual(len(names), len(manager.HashersManager._hasher_classes))

  def testGetHasherObject(self):
    """Tests the GetHasherObject function."""
    hasher_object = manager.HashersManager.GetHasherObject(u'md5')
    self.assertNotEqual(hasher_object, None)
    self.assertEqual(hasher_object.NAME, u'md5')

    hasher_object = manager.HashersManager.GetHasherObject(u'sha1')
    self.assertNotEqual(hasher_object, None)
    self.assertEqual(hasher_object.NAME, u'sha1')

    with self.assertRaises(KeyError):
      _ = manager.HashersManager.GetHasherObject(u'bogus')

  def testGetHasherObjects(self):
    """Tests getting hasher objects by name."""
    hasher_names = manager.HashersManager.GetHasherNames()
    hashers = manager.HashersManager.GetHasherObjects(hasher_names)
    self.assertEqual(len(hasher_names), len(hashers))
    for hasher in hashers:
      self.assertIsInstance(hasher, interface.BaseHasher)


if __name__ == '__main__':
  unittest.main()
