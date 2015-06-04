#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Windows XML EventLog (EVTX) file event formatter."""

import unittest

from plaso.formatters import winevtx

from tests.formatters import test_lib


class WinEVTXFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Windows XML EventLog (EVTX) record event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = winevtx.WinEVTXFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = winevtx.WinEVTXFormatter()

    expected_attribute_names = [
        u'event_identifier',
        u'record_number',
        u'event_level',
        u'source_name',
        u'computer_name',
        u'message_string',
        u'strings']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
