#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows shell folders helper."""

import unittest

from plaso.helpers.windows import shell_folders

from tests import test_lib as shared_test_lib


class WindowsShellFoldersHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows shell folders helper."""

  def testGetDescription(self):
    """Tests the GetDescription function."""
    description = shell_folders.WindowsShellFoldersHelper.GetDescription(
        '3080f90d-d7ad-11d9-bd98-0000947b0257')
    self.assertEqual(description, 'Show Desktop')

    description = shell_folders.WindowsShellFoldersHelper.GetDescription(
        'bogus')
    self.assertIsNone(description)


if __name__ == '__main__':
  unittest.main()
