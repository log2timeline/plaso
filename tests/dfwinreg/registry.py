#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the Windows Registry library."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.dfwinreg import definitions
from plaso.dfwinreg import registry

from tests.dfwinreg import test_lib


class RegistryUnitTest(test_lib.WinRegTestCase):
  """Tests for the Windows Registry library."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._registry = registry.WinRegistry(
        backend=registry.WinRegistry.BACKEND_PYREGF)

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

  def _GetTestFileEntryFromPath(self, path_segments):
    """Creates a file entry that references a file in the test dir.

    Args:
      path_segments: the path segments inside the test data directory.

    Returns:
      A file entry object (instance of dfvfs.FileEntry).
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def _OpenWinRegFile(self, filename):
    """Opens a Windows Registry file.

    Args:
      filename: The filename of the Windows Registry file, relative to
                the test data location.

    Returns:
      A Windows Registry file object (instance of WinRegFile).
    """
    file_entry = self._GetTestFileEntryFromPath([filename])
    return self._registry.OpenFileEntry(file_entry)

  def testGetRegistryFileType(self):
    """Tests the GetRegistryFileType function."""
    winreg_file = self._OpenWinRegFile(u'NTUSER.DAT')

    registry_file_type = self._registry.GetRegistryFileType(winreg_file)
    self.assertEqual(
        registry_file_type, definitions.REGISTRY_FILE_TYPE_NTUSER)

    winreg_file.Close()

    winreg_file = self._OpenWinRegFile(u'SYSTEM')

    registry_file_type = self._registry.GetRegistryFileType(winreg_file)
    self.assertEqual(
        registry_file_type, definitions.REGISTRY_FILE_TYPE_SYSTEM)

    winreg_file.Close()


if __name__ == '__main__':
  unittest.main()
