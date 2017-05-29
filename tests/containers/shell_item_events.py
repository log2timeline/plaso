#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the shell item event attribute container."""

import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import shell_item_events

from tests import test_lib as shared_test_lib


class ShellItemFileEntryEventTest(shared_test_lib.BaseTestCase):
  """Tests for the shell item event attribute container."""

  def testGetAttributeNames(self):
    """Tests the GetAttributeNames function."""
    posix_time = dfdatetime_posix_time.PosixTime(timestamp=0)
    attribute_container = shell_item_events.ShellItemFileEntryEvent(
        posix_time, None, None, None, None, None, None, None)

    expected_attribute_names = [
        u'data_type', u'display_name', u'file_reference', u'filename',
        u'hostname', u'inode', u'localized_name', u'long_name', u'name',
        u'offset', u'origin', u'pathspec', u'shell_item_path', u'tag',
        u'timestamp', u'timestamp_desc']

    attribute_names = sorted(attribute_container.GetAttributeNames())

    self.assertEqual(attribute_names, expected_attribute_names)


if __name__ == '__main__':
  unittest.main()
