#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the plist library functions."""

import unittest

from plaso.lib import plist

from tests import test_lib as shared_test_lib


class PlistTests(shared_test_lib.BaseTestCase):
  """Class to test the plist file."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.HIToolbox.plist'])
  def testGetValueByPath(self):
    """Tests the GetValueByPath function."""
    test_file_path = self._GetTestFilePath([u'com.apple.HIToolbox.plist'])

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      path_segments = [
          u'AppleEnabledInputSources', u'0', u'KeyboardLayout Name']

      plist_value = plist_file.GetValueByPath(path_segments)
      self.assertEqual(plist_value, u'U.S.')

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.HIToolbox.plist'])
  def testReadBinary(self):
    """Tests the Read function on a binary plist file."""
    test_file_path = self._GetTestFilePath([u'com.apple.HIToolbox.plist'])

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.iPod.plist'])
  def testReadXML(self):
    """Tests the Read function on a XML plist file."""
    test_file_path = self._GetTestFilePath([u'com.apple.iPod.plist'])

    with open(test_file_path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)


if __name__ == '__main__':
  unittest.main()
