#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Analytics cookies."""

import unittest

from plaso.parsers.cookie_plugins import ganalytics  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import chrome_cookies
from plaso.parsers.sqlite_plugins import firefox_cookies

from tests.parsers.sqlite_plugins import test_lib as sqlite_plugins_test_lib


class GoogleAnalyticsPluginTest(sqlite_plugins_test_lib.SQLitePluginTestCase):
  """Tests for the Google Analytics plugin."""

  def testParsingFirefox29CookieDatabase(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookie2Plugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_cookies.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 105)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'cookie_name': '__utmz',
        'data_type': 'cookie:google:analytics:utmz',
        'domain_hash': '137167072',
        'last_visited_time': '2013-10-30T21:56:06+00:00',
        'sessions': 1,
        'sources': 1,
        'url': 'http://ads.aha.is/',
        'utmccn': '(referral)',
        'utmcct': (
            '/frettir/erlent/2013/10/30/maelt_med_kerfisbundnum_hydingum/'),
        'utmcmd': 'referral',
        'utmcsr': 'mbl.is'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 48)
    self.CheckEventData(event_data, expected_event_values)

  def testParsingChromeCookieDatabase(self):
    """Test the process function on a Chrome cookie database."""
    plugin = chrome_cookies.Chrome17CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['cookies.db'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 603)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    # Check an UTMZ Google Analytics entry.
    expected_event_values = {
        'cookie_name': '__utmz',
        'data_type': 'cookie:google:analytics:utmz',
        'domain_hash': '68898382',
        'last_visited_time': '2012-03-22T01:57:06+00:00',
        'sessions': 1,
        'sources': 1,
        'url': 'http://imdb.com/',
        'utmccn': '(organic)',
        'utmctr': 'enders game',
        'utmcmd': 'organic',
        'utmcsr': 'google'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 287)
    self.CheckEventData(event_data, expected_event_values)

    # Check an UTMA Google Analytics entry.
    expected_event_values = {
        'cookie_name': '__utma',
        'data_type': 'cookie:google:analytics:utma',
        'domain_hash': '151488169',
        'sessions': 2,
        'url': 'http://assets.tumblr.com/',
        'visited_times': [
           '2012-03-22T01:55:29+00:00',
           '2012-03-22T01:55:29+00:00',
           '2012-04-01T13:31:52+00:00'],
        'visitor_identifier': '1827102436'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 329)
    self.CheckEventData(event_data, expected_event_values)

    # Check an UTMB Google Analytics entry.
    expected_event_values = {
        'cookie_name': '__utmb',
        'data_type': 'cookie:google:analytics:utmb',
        'domain_hash': '154523900',
        'last_visited_time': '2012-03-22T01:48:30+00:00',
        'pages_viewed': 1,
        'url': 'http://upressonline.com/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 180)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
