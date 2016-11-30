#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zsh extended_history formatter."""

import unittest

from tests.formatters import test_lib
from plaso.formatters import bash_history
from plaso.parsers import bash_history as bash_parser


class BashHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Bash history event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._formatter = bash_history.BashHistoryFormatter()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    expected_attribute_names = [u'command']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    mediator = None
    event = bash_parser.BashEvent(1457771210, u'cd plaso')

    expected_messages = (u'Command executed: cd plaso', u'cd plaso')
    messages = self._formatter.GetMessages(mediator, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
