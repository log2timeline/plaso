#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the SAM users Windows Registry event formatter."""

import unittest

from plaso.formatters import sam_users

from tests.formatters import test_lib


class SAMUsersWindowsRegistryEventFormatterTest(
    test_lib.EventFormatterTestCase):
  """Tests for the SAM users Windows Registry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = sam_users.SAMUsersWindowsRegistryEventFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = sam_users.SAMUsersWindowsRegistryEventFormatter()

    expected_attribute_names = [
        u'account_rid',
        u'comments',
        u'fullname',
        u'key_path',
        u'login_count',
        u'username']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
