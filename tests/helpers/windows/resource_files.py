#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows PE/COFF resource file helper."""

import unittest

from plaso.helpers.windows import resource_files

from tests import test_lib as shared_test_lib


class WindowsResourceFileHelperTest(shared_test_lib.BaseTestCase):
  """Tests for the Windows PE/COFF resource file helper."""

  def testFormatMessageStringInPEP3101(self):
    """Tests the FormatMessageStringInPEP3101 function."""
    test_helper = resource_files.WindowsResourceFileHelper

    original_message_string = (
        'Sync info for %1%nServer copy exists, client copy replaced then '
        'deleted.%n%10\\%nSee details for more information.')
    message_string = test_helper.FormatMessageStringInPEP3101(
        original_message_string)

    expected_message_string = (
        'Sync info for {0:s}\\nServer copy exists, client copy replaced then '
        'deleted.\\n{9:s}\\\\nSee details for more information.')
    self.assertEqual(message_string, expected_message_string)


if __name__ == '__main__':
  unittest.main()
