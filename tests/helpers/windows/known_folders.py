#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows known folders helper."""

import unittest

from plaso.helpers.windows import known_folders

from tests import test_lib as shared_test_lib


class WindowsKnownFoldersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows known folders helper."""

  def testGetPath(self):
    """Tests the GetPath function."""
    path = known_folders.WindowsKnownFoldersHelper.GetPath(
        '{b4bfcc3a-db2c-424c-b029-7fe99a87c641}')
    self.assertEqual(path, '%USERPROFILE%\\Desktop')

    path = known_folders.WindowsKnownFoldersHelper.GetPath('bogus')
    self.assertIsNone(path)


if __name__ == '__main__':
  unittest.main()
