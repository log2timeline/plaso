#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest (popcontest) parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import popcontest as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import popcontest

from tests.parsers import test_lib


class PopularityContestUnitTest(test_lib.ParserTestCase):
  """Tests for the popcontest parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = popcontest.PopularityContestParser()
    storage_writer = self._ParseFile(['popcontest1.log'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 22)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2010-06-22 05:41:41.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Session 0 start '
        'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_message = 'Session 0 start'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[1]

    self.CheckTimestamp(event.timestamp, '2010-06-22 07:34:42.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'mru [/usr/sbin/atd] package [at]'
    expected_short_message = '/usr/sbin/atd'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[3]

    self.CheckTimestamp(event.timestamp, '2010-06-22 07:34:43.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'mru [/usr/lib/python2.5/lib-dynload/_struct.so] '
        'package [python2.5-minimal]')
    expected_short_message = '/usr/lib/python2.5/lib-dynload/_struct.so'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[5]

    self.CheckTimestamp(event.timestamp, '2010-05-30 05:26:20.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_message = '/usr/bin/empathy'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[6]

    self.CheckTimestamp(event.timestamp, '2010-05-30 05:27:43.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_message = '/usr/bin/empathy'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[11]

    self.CheckTimestamp(event.timestamp, '2010-05-12 07:58:33.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'mru [/usr/bin/orca] package [gnome-orca] tag [OLD]'
    expected_short_message = '/usr/bin/orca'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[13]

    self.CheckTimestamp(event.timestamp, '2010-06-22 05:41:41.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Session 0 end'
    expected_short_message = expected_message
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[14]

    self.CheckTimestamp(event.timestamp, '2010-06-22 05:41:41.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Session 1 start '
        'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_message = 'Session 1 start'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[15]

    self.CheckTimestamp(event.timestamp, '2010-06-22 07:34:42.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'mru [/super/cool/plasuz] package [plaso]'
    expected_short_message = '/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[18]

    self.CheckTimestamp(event.timestamp, '2010-04-06 12:25:42.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'mru [/super/cool/plasuz] package [miss_ctime]'
    expected_short_message = '/super/cool/plasuz'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[19]

    self.CheckTimestamp(event.timestamp, '2010-05-12 07:58:33.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_ACCESS)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'mru [/super/cóól] package [plaso] tag [WRONG_TAG]'
    expected_short_message = '/super/cóól'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    event = events[21]

    self.CheckTimestamp(event.timestamp, '2010-06-22 05:41:41.000000')
    self.assertEqual(event.timestamp_desc, definitions.TIME_DESCRIPTION_ADDED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = 'Session 1 end'
    expected_short_message = expected_message
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
