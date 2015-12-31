#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

import os
import unittest

from plaso.dfwinreg import interface
from plaso.dfwinreg import regf
from plaso.dfwinreg import registry

from tests.dfwinreg import test_lib


class TestWinRegistryFileReader(interface.WinRegistryFileReader):
  """A single file Windows Registry file reader."""

  def Open(self, path, ascii_codepage=u'cp1252'):
    """Opens the Windows Registry file specified by the path.

    Args:
      path: the path of the Windows Registry file.
      ascii_codepage: optional ASCII string codepage.

    Returns:
      The Windows Registry file (instance of WinRegistryFile) or None.
    """
    registry_file = regf.REGFWinRegistryFile(ascii_codepage=ascii_codepage)
    file_object = open(path, 'rb')
    try:
      # If open is successful Registry file will manage the file object.
      registry_file.Open(file_object)
    except IOError:
      file_object.close()
      registry_file = None

    return registry_file


class RegistryTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry library."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._registry = registry.WinRegistry(
        registry_file_reader=TestWinRegistryFileReader())

  def _GetTestFilePath(self, path_segments):
    """Retrieves the path of a test file relative to the test data directory.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A path of the test file.
    """
    # Note that we need to pass the individual path segments to os.path.join
    # and not a list.
    return os.path.join(self._TEST_DATA_PATH, *path_segments)

  def testGetRegistryFileType(self):
    """Tests the GetRegistryFileType function."""
    test_path = self._GetTestFilePath([u'NTUSER.DAT'])
    registry_file = self._registry._OpenFile(test_path)

    key_path_prefix = self._registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, u'HKEY_CURRENT_USER')

    registry_file.Close()

    test_path = self._GetTestFilePath([u'SYSTEM'])
    registry_file = self._registry._OpenFile(test_path)

    key_path_prefix = self._registry.GetRegistryFileMapping(registry_file)
    self.assertEqual(key_path_prefix, u'HKEY_LOCAL_MACHINE\\System')

    registry_file.Close()


if __name__ == '__main__':
  unittest.main()
