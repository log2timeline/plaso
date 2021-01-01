#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the plist library functions."""

import unittest

from plaso.lib import plist

from tests import test_lib as shared_test_lib


class PlistTests(shared_test_lib.BaseTestCase):
  """Class to test the plist file."""

  def testGetValueByPath(self):
    """Tests the GetValueByPath function."""
    test_file_path = self._GetTestFilePath(['com.apple.HIToolbox.plist'])
    self._SkipIfPathNotExists(test_file_path)

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      path_segments = [
          'AppleEnabledInputSources', '0', 'KeyboardLayout Name']

      plist_value = plist_file.GetValueByPath(path_segments)
      self.assertEqual(plist_value, 'U.S.')

  def testReadBinary(self):
    """Tests the Read function on a binary plist file."""
    test_file_path = self._GetTestFilePath(['com.apple.HIToolbox.plist'])
    self._SkipIfPathNotExists(test_file_path)

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)

  def testReadXML(self):
    """Tests the Read function on a XML plist file."""
    test_file_path = self._GetTestFilePath(['com.apple.iPod.plist'])
    self._SkipIfPathNotExists(test_file_path)

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)


if __name__ == '__main__':
  unittest.main()
