#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari cookie parser."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import safari_cookies as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import safari_cookies

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SafariCookieParserTest(test_lib.ParserTestCase):
  """Tests for the Safari cookie parser."""

  @shared_test_lib.skipUnlessHasTestFile(['Cookies.binarycookies'])
  def testParseFile(self):
    """Tests the Parse function on a Safari binary cookies file."""
    parser = safari_cookies.BinaryCookieParser()
    storage_writer = self._ParseFile(
        ['Cookies.binarycookies'], parser)

    cookie_events = []
    for event in storage_writer.GetEvents():
      if event.data_type == 'safari:cookie:entry':
        cookie_events.append(event)

    # There should be:
    # * 207 events in total
    # * 182 events from the safari cookie parser
    # * 25 event from the cookie plugins
    self.assertEqual(storage_writer.number_of_events, 207)
    self.assertEqual(len(cookie_events), 182)

    event = cookie_events[3]
    self.assertEqual(event.flags, 5)
    self.assertEqual(event.url, 'accounts.google.com')
    self.assertEqual(event.cookie_name, 'GAPS')

    event = cookie_events[48]

    self.assertEqual(event.flags, 0)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-08 20:54:50')

    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.cookie_name, 'nonsession')
    self.assertEqual(event.path, '/')

    expected_message = '.ebay.com </> (nonsession)'
    expected_short_message = '.ebay.com (nonsession)'

    self._TestGetMessageStrings(
        event, expected_message, expected_short_message)

    event = cookie_events[52]
    self.assertEqual(event.cookie_name, 'fpc')
    value = (
        'd=0dTg3Ou32s3MrAJ2iHjFph100Tw3E1HTfDOTly0GfJ2g4W.mXpy54F9fjBFfXMw4YyW'
        'AG2cT2FVSqOvGGi_Y1OPrngmNvpKPPyz5gIUP6x_EQeM7bR3jsrg_F1UXVOgu6JgkFwqO'
        '5uHrv4HiL05qb.85Bl.V__HZI5wpAGOGPz1XHhY5mOMH.g.pkVDLli36W2iuYwA-&v=2')
    self.assertEqual(event.cookie_value, value)

    self.assertEqual(event.path, '/')
    self.assertEqual(event.url, '.www.yahoo.com')


if __name__ == '__main__':
  unittest.main()
