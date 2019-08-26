#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the Zsh extended_history parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import zsh_extended_history

from tests.parsers import test_lib


class ZshExtendedHistoryTest(test_lib.ParserTestCase):
  """Tests for the Zsh extended_history parser."""

  def testParse(self):
    """Tests for the Parse method."""
    parser = zsh_extended_history.ZshExtendedHistoryParser()
    storage_writer = self._ParseFile(['zsh_extended_history.txt'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2016-03-12 08:26:50.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.elapsed_seconds, 0)
    self.assertEqual(event_data.command, 'cd plaso')

    event = events[2]

    self.CheckTimestamp(event.timestamp, '2016-03-26 11:54:53.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.command, 'echo dfgdfg \\\\\n& touch /tmp/afile')

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2016-03-26 11:54:57.000000')

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    parser = zsh_extended_history.ZshExtendedHistoryParser()

    mediator = None
    valid_lines = ': 1457771210:0;cd plaso'
    self.assertTrue(parser.VerifyStructure(mediator, valid_lines))

    invalid_lines = ': 2016-03-26 11:54:53;0;cd plaso'
    self.assertFalse(parser.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()
