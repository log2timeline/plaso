#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Safari cookie parser."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import safari_cookies as safari_cookies_formatter
from plaso.lib import eventdata
from plaso.lib import timelib_test
from plaso.parsers import test_lib
from plaso.parsers import safari_cookies


class SafariCookieParserTest(test_lib.ParserTestCase):
  """Tests for the Safari cookie parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._parser = safari_cookies.BinaryCookieParser()

  def testParseFile(self):
    """Tests the Parse function on a version 17 Prefetch file."""
    test_file = self._GetTestFilePath([u'Cookies.binarycookies'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    # There should be 182 events from the safari cookie parser in addition
    # to those created by cookie plugins.
    self.assertTrue(len(event_objects) >= 182)

    cookie_events = []
    for event_object in event_objects:
      if isinstance(event_object, safari_cookies.BinaryCookieEvent):
        cookie_events.append(event_object)

    self.assertEquals(len(cookie_events), 182)

    event_object = cookie_events[3]
    self.assertEquals(event_object.flags, u'HttpOnly|Secure')
    self.assertEquals(event_object.url, u'accounts.google.com')
    self.assertEquals(event_object.cookie_name, u'GAPS')

    event_object = cookie_events[48]

    self.assertEquals(event_object.flags, u'')
    expected_timestamp = timelib_test.CopyStringToTimestamp(
        u'2013-07-08 20:54:50')

    self.assertEquals(event_object.timestamp, expected_timestamp)
    self.assertEquals(
        event_object.timestamp_desc, eventdata.EventTimestamp.CREATION_TIME)
    self.assertEquals(event_object.cookie_name, u'nonsession')
    self.assertEquals(event_object.path, u'/')

    expected_msg = u'.ebay.com </> (nonsession)'
    expected_msg_short = u'.ebay.com (nonsession)'

    self._TestGetMessageStrings(event_object, expected_msg, expected_msg_short)

    event_object = cookie_events[52]
    self.assertEquals(event_object.cookie_name, u'fpc')
    value = (
        u'd=0dTg3Ou32s3MrAJ2iHjFph100Tw3E1HTfDOTly0GfJ2g4W.mXpy54F9fjBFfXMw4YyW'
        u'AG2cT2FVSqOvGGi_Y1OPrngmNvpKPPyz5gIUP6x_EQeM7bR3jsrg_F1UXVOgu6JgkFwqO'
        u'5uHrv4HiL05qb.85Bl.V__HZI5wpAGOGPz1XHhY5mOMH.g.pkVDLli36W2iuYwA-&v=2')
    self.assertEquals(event_object.cookie_value, value)

    self.assertEquals(event_object.path, u'/')
    self.assertEquals(event_object.url, u'.www.yahoo.com')


if __name__ == '__main__':
  unittest.main()
