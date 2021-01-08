#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest (popcontest) parser."""

import unittest

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

    expected_event_values = {
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_message = (
        'Session 0 start '
        'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_message = 'Session 0 start'

    event_data = self._GetEventDataOfEvent(storage_writer, events[0])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 07:34:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_message = 'mru [/usr/sbin/atd] package [at]'
    expected_short_message = '/usr/sbin/atd'

    event_data = self._GetEventDataOfEvent(storage_writer, events[1])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 07:34:43.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_message = (
        'mru [/usr/lib/python2.5/lib-dynload/_struct.so] '
        'package [python2.5-minimal]')
    expected_short_message = '/usr/lib/python2.5/lib-dynload/_struct.so'

    event_data = self._GetEventDataOfEvent(storage_writer, events[3])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-05-30 05:26:20.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_message = (
        'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_message = '/usr/bin/empathy'

    event_data = self._GetEventDataOfEvent(storage_writer, events[5])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-05-30 05:27:43.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_message = (
        'mru [/usr/bin/empathy] package [empathy] tag [RECENT-CTIME]')
    expected_short_message = '/usr/bin/empathy'

    event_data = self._GetEventDataOfEvent(storage_writer, events[6])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-05-12 07:58:33.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_message = 'mru [/usr/bin/orca] package [gnome-orca] tag [OLD]'
    expected_short_message = '/usr/bin/orca'

    event_data = self._GetEventDataOfEvent(storage_writer, events[11])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[13], expected_event_values)

    expected_message = 'Session 0 end'
    expected_short_message = expected_message

    event_data = self._GetEventDataOfEvent(storage_writer, events[13])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    expected_message = (
        'Session 1 start '
        'ID 12345678901234567890123456789012 [ARCH:i386 POPCONVER:1.38]')
    expected_short_message = 'Session 1 start'

    event_data = self._GetEventDataOfEvent(storage_writer, events[14])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 07:34:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    expected_message = 'mru [/super/cool/plasuz] package [plaso]'
    expected_short_message = '/super/cool/plasuz'

    event_data = self._GetEventDataOfEvent(storage_writer, events[15])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-04-06 12:25:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_message = 'mru [/super/cool/plasuz] package [miss_ctime]'
    expected_short_message = '/super/cool/plasuz'

    event_data = self._GetEventDataOfEvent(storage_writer, events[18])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-05-12 07:58:33.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[19], expected_event_values)

    expected_message = 'mru [/super/cóól] package [plaso] tag [WRONG_TAG]'
    expected_short_message = '/super/cóól'

    event_data = self._GetEventDataOfEvent(storage_writer, events[19])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    expected_event_values = {
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)

    expected_message = 'Session 1 end'
    expected_short_message = expected_message

    event_data = self._GetEventDataOfEvent(storage_writer, events[21])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
