#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Java Cache IDX file parser."""

import unittest

from plaso.formatters import java_idx  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import java_idx

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class IDXTest(test_lib.ParserTestCase):
  """Tests for Java Cache IDX file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'java_602.idx'])
  def testParse602(self):
    """Tests the Parse function on a version 602 IDX file."""
    parser_object = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile([u'java_602.idx'], parser_object)

    self.assertEqual(len(storage_writer.events), 2)

    event_object = storage_writer.events[0]

    idx_version_expected = 602
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = u'Unknown'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = u'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event_object.url, url_expected)

    description_expected = u'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-05 01:34:19.720')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2010-05-05 03:52:31')
    self.assertEqual(event_object.timestamp, expected_timestamp)

  @shared_test_lib.skipUnlessHasTestFile([u'java.idx'])
  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    parser_object = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile([u'java.idx'], parser_object)

    self.assertEqual(len(storage_writer.events), 2)

    event_object = storage_writer.events[0]

    idx_version_expected = 605
    self.assertEqual(event_object.idx_version, idx_version_expected)

    ip_address_expected = u'10.7.119.10'
    self.assertEqual(event_object.ip_address, ip_address_expected)

    url_expected = (
        u'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        u'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event_object.url, url_expected)

    description_expected = u'File Hosted Date'
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2001-07-26 05:00:00')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    # Parse second event. Same metadata; different timestamp event.
    event_object = storage_writer.events[1]

    self.assertEqual(event_object.idx_version, idx_version_expected)
    self.assertEqual(event_object.ip_address, ip_address_expected)
    self.assertEqual(event_object.url, url_expected)

    description_expected = eventdata.EventTimestamp.FILE_DOWNLOADED
    self.assertEqual(event_object.timestamp_desc, description_expected)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-01-13 16:22:01')
    self.assertEqual(event_object.timestamp, expected_timestamp)


if __name__ == '__main__':
  unittest.main()
