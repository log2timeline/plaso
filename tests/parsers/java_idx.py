#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Java Cache IDX file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import java_idx as _  # pylint: disable=unused-import
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

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2010-05-05 01:34:19.720000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.idx_version, 602)

    expected_url = 'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_data.url, expected_url)

    description_expected = 'File Hosted Date'
    self.assertEqual(event.timestamp_desc, description_expected)

    # Parse second event. Same metadata; different timestamp event.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2010-05-05 03:52:31.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.idx_version, 602)

    expected_url = 'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_data.url, expected_url)

    description_expected = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, description_expected)

  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    parser = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile(['java.idx'], parser)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2001-07-26 05:00:00.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.idx_version, 605)
    self.assertEqual(event_data.ip_address, '10.7.119.10')

    expected_url = (
        'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_data.url, expected_url)

    description_expected = 'File Hosted Date'
    self.assertEqual(event.timestamp_desc, description_expected)

    # Parse second event. Same metadata; different timestamp event.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-01-13 16:22:01.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.idx_version, 605)
    self.assertEqual(event_data.ip_address, '10.7.119.10')

    expected_url = (
        'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_data.url, expected_url)

    description_expected = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, description_expected)


if __name__ == '__main__':
  unittest.main()
