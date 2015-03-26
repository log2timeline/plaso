#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Sleuthkit (TSK) bodyfile (or mactime) event formatter."""

import unittest

from plaso.formatters import mactime
from plaso.formatters import test_lib


class MactimeFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the mactime event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = mactime.MactimeFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = mactime.MactimeFormatter()

    expected_attribute_names = [u'filename']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
