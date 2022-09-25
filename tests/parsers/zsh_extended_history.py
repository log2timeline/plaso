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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 4)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'command': 'cd plaso',
        'data_type': 'shell:zsh:history',
        'date_time': '2016-03-12T08:26:50+00:00',
        'elapsed_seconds': 0}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'command': 'echo dfgdfg \\\\\n& touch /tmp/afile',
        'data_type': 'shell:zsh:history',
        'date_time': '2016-03-26T11:54:53+00:00',
        'elapsed_seconds': 0}

    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'data_type': 'shell:zsh:history',
        'date_time': '2016-03-26T11:54:57+00:00'}

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
