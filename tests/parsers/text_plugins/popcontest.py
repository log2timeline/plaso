#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Popularity Contest (popcontest) text parser plugin."""

import unittest

from plaso.lib import definitions
from plaso.parsers.text_plugins import popcontest

from tests.parsers.text_plugins import test_lib


class PopularityContestTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Popularity Contest (popcontest) text parser plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = popcontest.PopularityContestTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(['popcontest1.log'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 22)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # TODO: sort events.
    # events = list(storage_writer.GetSortedEvents())

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22T05:41:41+00:00',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '0',
        'status': 'start',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22T07:34:42+00:00',
        'mru': '/usr/sbin/atd',
        'package': 'at',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22T07:34:43+00:00',
        'mru': '/usr/lib/python2.5/lib-dynload/_struct.so',
        'package': 'python2.5-minimal',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-30T05:26:20+00:00',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-30T05:27:43+00:00',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp_desc': definitions.TIME_DESCRIPTION_METADATA_MODIFICATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-12T07:58:33+00:00',
        'mru': '/usr/bin/orca',
        'package': 'gnome-orca',
        'record_tag': 'OLD',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22T05:41:41+00:00',
        'session': '0',
        'status': 'end',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[13], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22T05:41:41+00:00',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '1',
        'status': 'start',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22T07:34:42+00:00',
        'mru': '/super/cool/plasuz',
        'package': 'plaso',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-04-06T12:25:42+00:00',
        'mru': '/super/cool/plasuz',
        'package': 'miss_ctime',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-12T07:58:33+00:00',
        'mru': '/super/cóól',
        'package': 'plaso',
        'record_tag': 'WRONG_TAG',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[19], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22T05:41:41+00:00',
        'session': '1',
        'status': 'end',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)


if __name__ == '__main__':
  unittest.main()
