#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookies."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import ganalytics as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.cookie_plugins import ganalytics  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import firefox_cookies

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
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type.startswith('cookie:google:analytics'):
        cookies.append(event)
    return cookies

  def testParsingFirefox29CookieDatabase(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_cookies.sqlite'], plugin)
    events = self._GetAnalyticsCookieEvents(storage_writer)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(len(events), 25)

    event = events[14]

    self.CheckTimestamp(event.timestamp, '2013-10-30 21:56:06.000000')

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    self.assertEqual(
        event_data.utmcct,
        '/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/')
    self.assertEqual(event_data.url, 'http://ads.aha.is/')
    self.assertEqual(event_data.utmcsr, 'mbl.is')

    expected_message = (
        'http://ads.aha.is/ (__utmz) Sessions: 1 Domain Hash: 137167072 '
        'Sources: 1 Last source used to access: mbl.is Ad campaign '
        'information: (referral) Last type of visit: referral Path to '
        'the page of referring link: /frettir/erlent/2013/10/30/'
        'maelt_med_kerfisbundnum_hydingum/')
    expected_short_message = 'http://ads.aha.is/ (__utmz)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.Chrome17CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['cookies.db'], plugin)
    events = self._GetAnalyticsCookieEvents(storage_writer)

    self.assertEqual(storage_writer.number_of_warnings, 0)

    # The cookie database contains 560 entries in total. Out of them
    # there are 75 events created by the Google Analytics plugin.
    self.assertEqual(len(events), 75)
    # Check few "random" events to verify.

    # Check an UTMZ Google Analytics event.
    event = events[39]

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.utmctr, 'enders game')
    self.assertEqual(event_data.domain_hash, '68898382')
    self.assertEqual(event_data.sessions, 1)

    expected_message = (
        'http://imdb.com/ (__utmz) Sessions: 1 Domain Hash: 68898382 '
        'Sources: 1 Last source used to access: google Ad campaign '
        'information: (organic) Last type of visit: organic Keywords '
        'used to find site: enders game')
    expected_short_message = 'http://imdb.com/ (__utmz)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the UTMA Google Analytics event.
    event = events[41]

    self.CheckTimestamp(event.timestamp, '2012-03-22 01:55:29.000000')
    self.assertEqual(event.timestamp_desc, 'Analytics Previous Time')

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.cookie_name, '__utma')
    self.assertEqual(event_data.visitor_id, '1827102436')
    self.assertEqual(event_data.sessions, 2)

    expected_message = (
        'http://assets.tumblr.com/ (__utma) '
        'Sessions: 2 '
        'Domain Hash: 151488169 '
        'Visitor ID: 1827102436')
    expected_short_message = 'http://assets.tumblr.com/ (__utma)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check the UTMB Google Analytics event.
    event = events[34]

    self.CheckTimestamp(event.timestamp, '2012-03-22 01:48:30.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_LAST_VISITED)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.cookie_name, '__utmb')
    self.assertEqual(event_data.domain_hash, '154523900')
    self.assertEqual(event_data.pages_viewed, 1)

    expected_message = (
        'http://upressonline.com/ (__utmb) Pages Viewed: 1 Domain Hash: '
        '154523900')
    expected_short_message = 'http://upressonline.com/ (__utmb)'

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
