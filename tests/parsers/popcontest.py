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
        'data_type': 'popularity_contest:session:event',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '0',
        'status': 'start',
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/usr/sbin/atd',
        'package': 'at',
        'timestamp': '2010-06-22 07:34:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/usr/lib/python2.5/lib-dynload/_struct.so',
        'package': 'python2.5-minimal',
        'timestamp': '2010-06-22 07:34:43.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp': '2010-05-30 05:26:20.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp': '2010-05-30 05:27:43.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/usr/bin/orca',
        'package': 'gnome-orca',
        'record_tag': 'OLD',
        'timestamp': '2010-05-12 07:58:33.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'session': '0',
        'status': 'end',
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[13], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '1',
        'status': 'start',
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/super/cool/plasuz',
        'package': 'plaso',
        'timestamp': '2010-06-22 07:34:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/super/cool/plasuz',
        'package': 'miss_ctime',
        'timestamp': '2010-04-06 12:25:42.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'mru': '/super/cóól',
        'package': 'plaso',
        'record_tag': 'WRONG_TAG',
        'timestamp': '2010-05-12 07:58:33.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[19], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'session': '1',
        'status': 'end',
        'timestamp': '2010-06-22 05:41:41.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)


if __name__ == '__main__':
  unittest.main()
