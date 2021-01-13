#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookies."""

import unittest

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

    expected_event_values = {
        'cookie_name': '__utmz',
        'data_type': 'cookie:google:analytics:utmz',
        'domain_hash': '137167072',
        'sessions': 1,
        'sources': 1,
        'timestamp': '2013-10-30 21:56:06.000000',
        'url': 'http://ads.aha.is/',
        'utmccn': '(referral)',
        'utmcct': (
            '/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/'),
        'utmcmd': 'referral',
        'utmcsr': 'mbl.is'}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.Chrome17CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['cookies.db'], plugin)
    events = self._GetAnalyticsCookieEvents(storage_writer)

    self.assertEqual(storage_writer.number_of_warnings, 0)

    # The cookie database contains 560 entries in total. Out of them
    # there are 75 events created by the Google Analytics plugin.
    self.assertEqual(len(events), 75)
    # Check few "random" events to verify.

    # Check an UTMZ Google Analytics event.
    expected_event_values = {
        'cookie_name': '__utmz',
        'data_type': 'cookie:google:analytics:utmz',
        'domain_hash': '68898382',
        'sessions': 1,
        'sources': 1,
        'url': 'http://imdb.com/',
        'utmccn': '(organic)',
        'utmctr': 'enders game',
        'utmcmd': 'organic',
        'utmcsr': 'google'}

    self.CheckEventValues(storage_writer, events[39], expected_event_values)

    # Check the UTMA Google Analytics event.
    expected_event_values = {
        'cookie_name': '__utma',
        'data_type': 'cookie:google:analytics:utma',
        'domain_hash': '151488169',
        'sessions': 2,
        'timestamp': '2012-03-22 01:55:29.000000',
        'timestamp_desc': 'Analytics Previous Time',
        'url': 'http://assets.tumblr.com/',
        'visitor_id': '1827102436'}

    self.CheckEventValues(storage_writer, events[41], expected_event_values)

    # Check the UTMB Google Analytics event.
    expected_event_values = {
        'cookie_name': '__utmb',
        'data_type': 'cookie:google:analytics:utmb',
        'domain_hash': '154523900',
        'pages_viewed': 1,
        'timestamp': '2012-03-22 01:48:30.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'url': 'http://upressonline.com/'}

    self.CheckEventValues(storage_writer, events[34], expected_event_values)


if __name__ == '__main__':
  unittest.main()
