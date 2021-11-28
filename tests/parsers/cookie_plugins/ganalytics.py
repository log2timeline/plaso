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

  def testParsingFirefox29CookieDatabase(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_cookies.sqlite'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 295)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    cookie_events = []
    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type.startswith('cookie:google:analytics'):
        cookie_events.append(event)

    self.assertEqual(len(cookie_events), 25)

    expected_event_values = {
        'cookie_name': '__utmz',
        'data_type': 'cookie:google:analytics:utmz',
        'date_time': '2013-10-30 21:56:06',
        'domain_hash': '137167072',
        'sessions': 1,
        'sources': 1,
        'url': 'http://ads.aha.is/',
        'utmccn': '(referral)',
        'utmcct': (
            '/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/'),
        'utmcmd': 'referral',
        'utmcsr': 'mbl.is'}

    self.CheckEventValues(
        storage_writer, cookie_events[14], expected_event_values)

  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.Chrome17CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['cookies.db'], plugin)

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 1755)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    cookie_events = []
    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type.startswith('cookie:google:analytics'):
        cookie_events.append(event)

    # There are 75 events created by the Google Analytics plugin.
    self.assertEqual(len(cookie_events), 75)

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

    self.CheckEventValues(
        storage_writer, cookie_events[39], expected_event_values)

    # Check the UTMA Google Analytics event.
    expected_event_values = {
        'cookie_name': '__utma',
        'data_type': 'cookie:google:analytics:utma',
        'date_time': '2012-03-22 01:55:29',
        'domain_hash': '151488169',
        'sessions': 2,
        'timestamp_desc': 'Analytics Previous Time',
        'url': 'http://assets.tumblr.com/',
        'visitor_id': '1827102436'}

    self.CheckEventValues(
        storage_writer, cookie_events[41], expected_event_values)

    # Check the UTMB Google Analytics event.
    expected_event_values = {
        'cookie_name': '__utmb',
        'data_type': 'cookie:google:analytics:utmb',
        'date_time': '2012-03-22 01:48:30',
        'domain_hash': '154523900',
        'pages_viewed': 1,
        'timestamp_desc': definitions.TIME_DESCRIPTION_LAST_VISITED,
        'url': 'http://upressonline.com/'}

    self.CheckEventValues(
        storage_writer, cookie_events[34], expected_event_values)


if __name__ == '__main__':
  unittest.main()
