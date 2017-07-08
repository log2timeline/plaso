#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookies."""

import unittest

from plaso.formatters import ganalytics  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.cookie_plugins import ganalytics
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import firefox_cookies

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib as sqlite_plugins_test_lib


class GoogleAnalyticsPluginTest(sqlite_plugins_test_lib.SQLitePluginTestCase):
  """Tests for the Google Analytics plugin."""

  def _GetAnalyticsCookieEvents(self, storage_writer):
    """Retrieves the analytics cookie events.

    Returns:
      list[EventObject]: analytics cookie events.
    """
    cookies = []
    for event in storage_writer.GetEvents():
      if event.data_type.startswith(u'cookie:google:analytics'):
        cookies.append(event)
    return cookies

  @shared_test_lib.skipUnlessHasTestFile([u'firefox_cookies.sqlite'])
  def testParsingFirefox29CookieDatabase(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'firefox_cookies.sqlite'], plugin)
    events = self._GetAnalyticsCookieEvents(storage_writer)

    self.assertEqual(len(events), 25)

    event = events[14]

    self.assertEqual(
        event.utmcct,
        u'/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/')
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-30 21:56:06')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.url, u'http://ads.aha.is/')
    self.assertEqual(event.utmcsr, u'mbl.is')

    expected_message = (
        u'http://ads.aha.is/ (__utmz) Sessions: 1 Domain Hash: 137167072 '
        u'Sources: 1 Last source used to access: mbl.is Ad campaign '
        u'information: (referral) Last type of visit: referral Path to '
        u'the page of referring link: /frettir/erlent/2013/10/30/'
        u'maelt_med_kerfisbundnum_hydingum/')
    expected_short_message = u'http://ads.aha.is/ (__utmz)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

  @shared_test_lib.skipUnlessHasTestFile([u'cookies.db'])
  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.ChromeCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'cookies.db'], plugin)
    events = self._GetAnalyticsCookieEvents(storage_writer)

    # The cookie database contains 560 entries in total. Out of them
    # there are 75 events created by the Google Analytics plugin.
    self.assertEqual(len(events), 75)
    # Check few "random" events to verify.

    # Check an UTMZ Google Analytics event.
    event = events[39]
    self.assertEqual(event.utmctr, u'enders game')
    self.assertEqual(event.domain_hash, u'68898382')
    self.assertEqual(event.sessions, 1)

    expected_message = (
        u'http://imdb.com/ (__utmz) Sessions: 1 Domain Hash: 68898382 '
        u'Sources: 1 Last source used to access: google Ad campaign '
        u'information: (organic) Last type of visit: organic Keywords '
        u'used to find site: enders game')
    expected_short_message = u'http://imdb.com/ (__utmz)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the UTMA Google Analytics event.
    event = events[41]
    self.assertEqual(event.timestamp_desc, u'Analytics Previous Time')
    self.assertEqual(event.cookie_name, u'__utma')
    self.assertEqual(event.visitor_id, u'1827102436')
    self.assertEqual(event.sessions, 2)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-22 01:55:29')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'http://assets.tumblr.com/ (__utma) '
        u'Sessions: 2 '
        u'Domain Hash: 151488169 '
        u'Visitor ID: 1827102436')
    expected_short_message = u'http://assets.tumblr.com/ (__utma)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check the UTMB Google Analytics event.
    event = events[34]
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)
    self.assertEqual(event.cookie_name, u'__utmb')
    self.assertEqual(event.domain_hash, u'154523900')
    self.assertEqual(event.pages_viewed, 1)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2012-03-22 01:48:30')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'http://upressonline.com/ (__utmb) Pages Viewed: 1 Domain Hash: '
        u'154523900')
    expected_short_message = u'http://upressonline.com/ (__utmb)'

    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
