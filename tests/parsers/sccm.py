#!/usr/bin/python
# -*_ coding: utf-8 -*-
"""Tests for the SCCM Logs Parser."""

import unittest

from plaso.formatters import sccm as _ # pylint: disable=unused-import
from plaso.parsers import sccm
from tests.parsers import test_lib
from plaso.lib import timelib


class SCCMLogsUnitTest(test_lib.ParserTestCase):
  """Tests for the SCCM Logs Parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = sccm.SCCMParser()

  def testParse(self):
    """Tests for the Parse function."""
    test_file = self._GetTestFilePath([u'sccm_various.log'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 10)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-28 14:03:19.766')
    self.assertEqual(event_objects[0].timestamp, expected_timestamp)

    # Test timestamps with seven digits after seconds.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-01-02 10:22:50.873496')
    self.assertEqual(event_objects[3].timestamp, expected_timestamp)

    # Test timestamps with '-' in microseconds.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-12-28 07:59:43.373')
    self.assertEqual(event_objects[7].timestamp, expected_timestamp)

    # Test timestamps with '+' in microseconds.
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2014-11-24 09:52:13.827')
    self.assertEqual(event_objects[9].timestamp, expected_timestamp)

    # Test full and short message formats.
    expected_msg = (
        u'ContentAccess Releasing content request '
        u'{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    expected_msg_short = (
        u'Releasing content request '
        u'{4EA97AD6-E7E2-4583-92B9-21F532501337}')

    self._TestGetMessageStrings(
        event_objects[4], expected_msg, expected_msg_short)


if __name__ == '__main__':
  unittest.main()
