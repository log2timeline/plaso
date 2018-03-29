#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for Java Cache IDX file parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import java_idx as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers import java_idx

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class IDXTest(test_lib.ParserTestCase):
  """Tests for Java Cache IDX file parser."""

  @shared_test_lib.skipUnlessHasTestFile(['java_602.idx'])
  def testParse602(self):
    """Tests the Parse function on a version 602 IDX file."""
    parser = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile(['java_602.idx'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2010-05-05 01:34:19.720000')

    idx_version_expected = 602
    self.assertEqual(event.idx_version, idx_version_expected)

    ip_address_expected = 'Unknown'
    self.assertEqual(event.ip_address, ip_address_expected)

    url_expected = 'http://www.gxxxxx.com/a/java/xxz.jar'
    self.assertEqual(event.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event.timestamp_desc, description_expected)

    # Parse second event. Same metadata; different timestamp event.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2010-05-05 03:52:31.000000')

    self.assertEqual(event.idx_version, idx_version_expected)
    self.assertEqual(event.ip_address, ip_address_expected)
    self.assertEqual(event.url, url_expected)

    description_expected = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, description_expected)

  @shared_test_lib.skipUnlessHasTestFile(['java.idx'])
  def testParse605(self):
    """Tests the Parse function on a version 605 IDX file."""
    parser = java_idx.JavaIDXParser()
    storage_writer = self._ParseFile(['java.idx'], parser)

    self.assertEqual(storage_writer.number_of_events, 2)

    events = list(storage_writer.GetEvents())

    event = events[0]

    self.CheckTimestamp(event.timestamp, '2001-07-26 05:00:00.000000')

    idx_version_expected = 605
    self.assertEqual(event.idx_version, idx_version_expected)

    ip_address_expected = '10.7.119.10'
    self.assertEqual(event.ip_address, ip_address_expected)

    url_expected = (
        'http://xxxxc146d3.gxhjxxwsf.xx:82/forum/dare.php?'
        'hsh=6&key=b30xxxx1c597xxxx15d593d3f0xxx1ab')
    self.assertEqual(event.url, url_expected)

    description_expected = 'File Hosted Date'
    self.assertEqual(event.timestamp_desc, description_expected)

    # Parse second event. Same metadata; different timestamp event.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2013-01-13 16:22:01.000000')

    self.assertEqual(event.idx_version, idx_version_expected)
    self.assertEqual(event.ip_address, ip_address_expected)
    self.assertEqual(event.url, url_expected)

    description_expected = definitions.TIME_DESCRIPTION_FILE_DOWNLOADED
    self.assertEqual(event.timestamp_desc, description_expected)


if __name__ == '__main__':
  unittest.main()
