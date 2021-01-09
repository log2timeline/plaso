#!/usr/bin/env python3
# -*_ coding: utf-8 -*-
"""Tests for the Zsh extended_history parser."""

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

    expected_event_values = {
        'command': 'cd plaso',
        'data_type': 'shell:zsh:history',
        'elapsed_seconds': 0,
        'timestamp': '2016-03-12 08:26:50.000000'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'command': 'echo dfgdfg \\\\\n& touch /tmp/afile',
        'data_type': 'shell:zsh:history',
        'elapsed_seconds': 0,
        'timestamp': '2016-03-26 11:54:53.000000'}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'shell:zsh:history',
        'timestamp': '2016-03-26 11:54:57.000000'}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    mediator = None
    parser = zsh_extended_history.ZshExtendedHistoryParser()

    valid_lines = ': 1457771210:0;cd plaso'
    self.assertTrue(parser.VerifyStructure(mediator, valid_lines))

    invalid_lines = ': 2016-03-26 11:54:53;0;cd plaso'
    self.assertFalse(parser.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()
