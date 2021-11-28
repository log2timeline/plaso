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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 22)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22 05:41:41',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '0',
        'status': 'start',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22 07:34:42',
        'mru': '/usr/sbin/atd',
        'package': 'at',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22 07:34:43',
        'mru': '/usr/lib/python2.5/lib-dynload/_struct.so',
        'package': 'python2.5-minimal',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[3], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-30 05:26:20',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[5], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-30 05:27:43',
        'mru': '/usr/bin/empathy',
        'package': 'empathy',
        'record_tag': 'RECENT-CTIME',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION}

    self.CheckEventValues(storage_writer, events[6], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-12 07:58:33',
        'mru': '/usr/bin/orca',
        'package': 'gnome-orca',
        'record_tag': 'OLD',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[11], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22 05:41:41',
        'session': '0',
        'status': 'end',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[13], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22 05:41:41',
        'details': 'ARCH:i386 POPCONVER:1.38',
        'hostid': '12345678901234567890123456789012',
        'session': '1',
        'status': 'start',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-06-22 07:34:42',
        'mru': '/super/cool/plasuz',
        'package': 'plaso',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[15], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-04-06 12:25:42',
        'mru': '/super/cool/plasuz',
        'package': 'miss_ctime',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:log:event',
        'date_time': '2010-05-12 07:58:33',
        'mru': '/super/cóól',
        'package': 'plaso',
        'record_tag': 'WRONG_TAG',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_ACCESS}

    self.CheckEventValues(storage_writer, events[19], expected_event_values)

    expected_event_values = {
        'data_type': 'popularity_contest:session:event',
        'date_time': '2010-06-22 05:41:41',
        'session': '1',
        'status': 'end',
        'timestamp_desc': definitions.TIME_DESCRIPTION_ADDED}

    self.CheckEventValues(storage_writer, events[21], expected_event_values)


if __name__ == '__main__':
  unittest.main()
