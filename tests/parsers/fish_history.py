
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Fish History file parser."""

import unittest

from plaso.parsers import fish_history

from tests.parsers import test_lib


class FishHistoryTest(test_lib.ParserTestCase):
  """Tests for Fish History file parser."""

  def testParseFile(self):
    """Test parsing of a Fish History file."""
    parser = fish_history.FishHistoryParser()
    storage_writer = self._ParseFile(['fish_history'], parser)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 10)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'command': 'll', 'date_time': '2021-04-29 22:53:00'}
    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'command': 'la', 'date_time': '2021-04-29 22:53:02'}
    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'command': 'mkdir test', 'date_time': '2021-04-29 22:53:24'}
    self.CheckEventValues(storage_writer, events[2], expected_event_values)

    expected_event_values = {
        'command': 'cp *.txt test', 'date_time': '2021-04-29 22:53:32'}
    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'command': 'cd test', 'date_time': '2021-04-29 22:53:37'}
    self.CheckEventValues(storage_writer, events[4], expected_event_values)

    expected_event_values = {
        'command': 'rm -rf test', 'date_time': '2021-04-29 22:54:18'}
    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'command': 'clear', 'date_time': '2021-05-03 08:20:14'}
    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'command': 'pwd', 'date_time': '2021-05-03 19:08:19'}
    self.CheckEventValues(storage_writer, events[7], expected_event_values)

    expected_event_values = {
        'command': 'git clone git@github.com:log2timeline/plaso.git',
        'date_time': '2021-07-11 02:58:01'}
    self.CheckEventValues(storage_writer, events[8], expected_event_values)

    expected_event_values = {
        'command': 'cd plaso', 'date_time': '2021-07-11 02:58:35'}
    self.CheckEventValues(storage_writer, events[9], expected_event_values)


if __name__ == '__main__':
  unittest.main()
