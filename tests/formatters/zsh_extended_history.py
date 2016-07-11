#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zsh extended_history formatter."""

import unittest

from tests.formatters import test_lib
from plaso.formatters import zsh_extended_history
from plaso.parsers import zsh_extended_history as zsh_parser


class ZshExtendedHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Zsh extended_history event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._formatter = zsh_extended_history.ZshExtendedHistoryEventFormatter()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    expected_attribute_names = [
        u'command',
        u'elapsed_seconds']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    mediator = None
    event = zsh_parser.ZshHistoryEvent(1457771210, 0, u'cd plaso')

    expected_messages = (u'cd plaso Time elapsed: 0 seconds', u'cd plaso')
    messages = self._formatter.GetMessages(mediator, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
