#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the XChat scrollback file event formatter."""

import unittest

from plaso.formatters import xchatscrollback

from tests.formatters import test_lib


class XChatScrollbackFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the XChat scrollback file entry event formatter."""

  def testInitialization(self):
    """Tests the initialization."""
    event_formatter = xchatscrollback.XChatScrollbackFormatter()
    self.assertNotEqual(event_formatter, None)

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    event_formatter = xchatscrollback.XChatScrollbackFormatter()

    expected_attribute_names = [
        u'nickname',
        u'text']

    self._TestGetFormatStringAttributeNames(
        event_formatter, expected_attribute_names)

  # TODO: add test for GetMessages.


if __name__ == '__main__':
  unittest.main()
