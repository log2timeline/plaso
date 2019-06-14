#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Zsh extended_history formatter."""

from __future__ import unicode_literals

import unittest

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import time_events
from plaso.formatters import bash_history
from plaso.lib import definitions

from tests.formatters import test_lib


class BashHistoryFormatterTest(test_lib.EventFormatterTestCase):
  """Tests for the Bash history event formatter."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._formatter = bash_history.BashHistoryEventFormatter()

  def testGetFormatStringAttributeNames(self):
    """Tests the GetFormatStringAttributeNames function."""
    expected_attribute_names = ['command']

    self._TestGetFormatStringAttributeNames(
        self._formatter, expected_attribute_names)

  def testGetMessages(self):
    """Tests the GetMessages method."""
    date_time = dfdatetime_posix_time.PosixTime(timestamp=1457771210)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
    event.data_type = 'bash:history:command'
    event.command = 'cd plaso'

    expected_messages = ('Command executed: cd plaso', 'cd plaso')
    messages = self._formatter.GetMessages(None, event)
    self.assertEqual(messages, expected_messages)


if __name__ == '__main__':
  unittest.main()
