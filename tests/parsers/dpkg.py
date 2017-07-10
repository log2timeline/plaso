#!/usr/bin/python
# -*_ coding: utf-8 -*-
"""Tests for the dpkg.Log parser."""
import unittest

from plaso.lib import timelib
from plaso.parsers import dpkg

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class DpkgParserTest(test_lib.ParserTestCase):
  """Tests for the Dpkg Log parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'dpkg.log'])
  def testParse(self):
    """Tests for the Parse method."""
    parser = dpkg.DpkgParser()
    storage_writer = self._ParseFile([u'dpkg.log'], parser)

    self.assertEqual(storage_writer.number_of_events, 4)

    events = list(storage_writer.GetEvents())

    event = events[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2009-02-25 11:45:23')
    expected_body = u'conffile /etc/X11/Xsession keep'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.body, expected_body)

    event = events[1]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-08-03 15:25:53')
    expected_body = u'startup archives install'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.body, expected_body)

    event = events[2]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-08-06 17:35:39')
    expected_body = u'install base-passwd:amd64 <none> 3.5.33'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.body, expected_body)

    event = events[3]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-08-09 04:57:14')
    expected_body = u'status half-installed base-passwd:amd64 3.5.33'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.body, expected_body)

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    parser = dpkg.DpkgParser()

    mediator = None
    valid_lines = (
        u'2016-08-09 04:57:14 status half-installed base-passwd:amd64 3.5.33')
    self.assertTrue(parser.VerifyStructure(mediator, valid_lines))

    invalid_lines = (
        u'2016-08-09 04:57:14 X status half-installed base-passwd:amd64 3.5.33')
    self.assertFalse(parser.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()
