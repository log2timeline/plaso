#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari cookie parser."""

import unittest

from plaso.formatters import safari_cookies  # pylint: disable=unused-import
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import safari_cookies

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class SafariCookieParserTest(test_lib.ParserTestCase):
  """Tests for the Safari cookie parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'Cookies.binarycookies'])
  def testParseFile(self):
    """Tests the Parse function on a Safari binary cookies file."""
    parser_object = safari_cookies.BinaryCookieParser()
    storage_writer = self._ParseFile(
        [u'Cookies.binarycookies'], parser_object)

    cookie_events = []
    for event_object in storage_writer.events:
      if isinstance(event_object, safari_cookies.BinaryCookieEvent):
        cookie_events.append(event_object)

    # There should be:
    # * 207 events in total
    # * 182 events from the safari cookie parser
    # * 25 event from the cookie plugins
    self.assertEqual(len(storage_writer.events), 207)
    self.assertEqual(len(cookie_events), 182)

    event_object = cookie_events[3]
    self.assertEqual(event_object.flags, 5)
    self.assertEqual(event_object.url, u'accounts.google.com')
    self.assertEqual(event_object.cookie_name, u'GAPS')

    event_object = cookie_events[48]

    self.assertEqual(event_object.flags, 0)
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-07-08 20:54:50')

    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEqual(event_object.cookie_name, u'nonsession')
    self.assertEqual(event_object.path, u'/')

    expected_message = u'.ebay.com </> (nonsession)'
    expected_message_short = u'.ebay.com (nonsession)'

    self._TestGetMessageStrings(
        event_object, expected_message, expected_message_short)

    event_object = cookie_events[52]
    self.assertEqual(event_object.cookie_name, u'fpc')
    value = (
        u'd=0dTg3Ou32s3MrAJ2iHjFph100Tw3E1HTfDOTly0GfJ2g4W.mXpy54F9fjBFfXMw4YyW'
        u'AG2cT2FVSqOvGGi_Y1OPrngmNvpKPPyz5gIUP6x_EQeM7bR3jsrg_F1UXVOgu6JgkFwqO'
        u'5uHrv4HiL05qb.85Bl.V__HZI5wpAGOGPz1XHhY5mOMH.g.pkVDLli36W2iuYwA-&v=2')
    self.assertEqual(event_object.cookie_value, value)

    self.assertEqual(event_object.path, u'/')
    self.assertEqual(event_object.url, u'.www.yahoo.com')


if __name__ == '__main__':
  unittest.main()
