#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the UTMP binary file event formatter."""

import unittest

from plaso.formatters import test_lib
from plaso.formatters import utmpx


class UtmpxSessionFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the UTMP session event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = utmpx.UtmpxSessionFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = utmpx.UtmpxSessionFormatter()

    expected_attribute_names = [
        u'user',
        u'status',
        u'computer_name',
        u'terminal']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
