#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UTMP binary file event formatter."""

import unittest

from plaso.formatters import utmp

from tests.formatters import test_lib


class UtmpSessionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMP session event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = utmp.UtmpSessionFormatter()
    self.assertIsNotNone(event_formatter)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = utmp.UtmpSessionFormatter()

    expected_attribute_names = [
        u'user',
        u'computer_name',
        u'terminal',
        u'pid',
        u'terminal_id',
        u'status',
        u'ip_address',
        u'exit']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
