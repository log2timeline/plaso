#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the plist library functions."""

import os
import unittest

from plaso.lib import plist


class PlistTests(unittest.TestCase):
  """Class to test the plist file."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def testGetValueByPath(self):
    """Tests the GetValueByPath function."""
    path = os.path.join(u'test_data', u'com.apple.HIToolbox.plist')
    with open(path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      path_segments = [
          u'AppleEnabledInputSources', u'0', u'KeyboardLayout Name']

      plist_value = plist_file.GetValueByPath(path_segments)
      self.assertEqual(plist_value, u'U.S.')

  def testReadBinary(self):
    """Tests the Read function on a binary plist file."""
    path = os.path.join(u'test_data', u'com.apple.HIToolbox.plist')
    with open(path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)

  def testReadXML(self):
    """Tests the Read function on a XML plist file."""
    path = os.path.join(u'test_data', u'com.apple.iPod.plist')
    with open(path, 'rb') as file_object:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

      self.assertIsNotNone(plist_file.root_key)


if __name__ == '__main__':
  unittest.main()
