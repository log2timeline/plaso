#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Java Cache IDX file parser."""

import unittest

from plaso.lib import definitions
from plaso.parsers import java_idx

from tests.parsers import test_lib


class IDXTest(test_lib.ParserTestCase):
  """Tests for Java Cache IDX file parser."""

  def testParse602(self):
    """Tests the Parse function on a version 602 IDX file."""
    parser = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile(['java_602.idx'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'java:download:idx',
        'idx_version': 602,
        'timestamp': '2010-05-05 01:34:19.720000',
        'timestamp_desc': 'File Hosted Date',
        'url': 'http://www.gxxxxx.com/a/java/xxz.jar'}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Parse second event. Same metadata; different timestamp event.
    expected_event_values = {
        'data_type': 'java:download:idx',
        'idx_version': 602,
        'timestamp': '2010-05-05 03:52:31.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': 'http://www.gxxxxx.com/a/java/xxz.jar'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    parser = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile(['java.idx'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    expected_event_values = {
        'data_type': 'java:download:idx',
        'idx_version': 605,
        'ip_address': '10.7.119.10',
        'timestamp': '2001-07-26 05:00:00.000000',
        'timestamp_desc': 'File Hosted Date',
        'url': (
            'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
            'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')}

    self.CheckEventValues(storage_writer, events[0], expected_event_values)

    # Parse second event. Same metadata; different timestamp event.
    expected_event_values = {
        'data_type': 'java:download:idx',
        'idx_version': 605,
        'ip_address': '10.7.119.10',
        'timestamp': '2013-01-13 16:22:01.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_FILE_DOWNLOADED,
        'url': (
            'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
            'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)


if __name__ == '__main__':
  unittest.main()
