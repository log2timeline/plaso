#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the fake Windows Registry back-end."""

import unittest

from plaso.dfwinreg import fake

from tests.dfwinreg import test_lib


class FakeWinRegTestCase(test_lib.WinRegTestCase):
  """The unit test case for fake Windows Registry related object."""

  def _OpenFakeRegistryFile(self):
    """Opens a fake Windows Registry file.

    Returns:
      The Windows Registry file object (instance of FakeWinRegistryFileTest).
    """
    registry_file = fake.FakeWinRegistryFile()

    software_key = fake.FakeWinRegistryKey(u'Software')
    result = registry_file.AddKeyByPath(u'\\', software_key)
    self.assertTrue(result)

    registry_file.Open(None)
    return registry_file


class FakeWinRegistryFileTest(FakeWinRegTestCase):
  """Tests for the fake Windows Registry file object."""

  def testOpenClose(self):
    """Tests the Open and Close functions."""
    registry_file = self._OpenFakeRegistryFile()
    registry_file.Close()

  def testGetRootKey(self):
    """Tests the GetRootKey function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_key = registry_file.GetRootKey()
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, u'\\')

    registry_file.Close()

  def testGetKeyByPath(self):
    """Tests the GetKeyByPath function."""
    registry_file = self._OpenFakeRegistryFile()

    key_path = u'\\'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    key_path = u'\\Software'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNotNone(registry_key)
    self.assertEqual(registry_key.path, key_path)

    key_path = u'\\Bogus'
    registry_key = registry_file.GetKeyByPath(key_path)
    self.assertIsNone(registry_key)

    registry_file.Close()

  def testRecurseKeys(self):
    """Tests the RecurseKeys function."""
    registry_file = self._OpenFakeRegistryFile()

    registry_keys = list(registry_file.RecurseKeys())
    registry_file.Close()

    self.assertEqual(len(registry_keys), 2)

# TODO: add key tests.
# TODO: add value tests.


if __name__ == '__main__':
  unittest.main()
