#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Windows Restore Point (rp.log) file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import winrestore as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import winrestore

from tests.parsers import test_lib


class RestorePointLogParserTest(test_lib.ParserTestCase):
  """Tests for the Windows Restore Point (rp.log) file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = winrestore.RestorePointLogParser()
    storage_writer = self._ParseFile(['rp.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'description': 'Software Distribution Service 3.0',
        'restore_point_event_type': 102,
        'restore_point_type': 0,
        'timestamp': '2015-03-23 18:38:14.246954',
        'timestamp_desc': definitions.TIME_DESCRIPTION_CREATION}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Software Distribution Service 3.0 '
        'Event type: BEGIN_NESTED_SYSTEM_CHANGE '
        'Restore point type: APPLICATION_INSTALL')
    expected_short_message = (
        'Software Distribution Service 3.0')

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
