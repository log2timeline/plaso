#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Google Chrome cookie database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import chrome_cookies

from tests.parsers.sqlite_plugins import test_lib


class Chrome17CookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 17-65 cookie database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome cookie database file."""
    plugin = chrome_cookies.Chrome17CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(['cookies.db'], plugin)

    # 560 Chrome cookie and 43 cookie plugin.
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 603)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2011-08-25T21:50:27.292367+00:00',
        'creation_time': '2011-08-25T21:48:20.792703+00:00',
        'cookie_name': 'leo_auth_token',
        'data': (
            '"LIM:137381921:a:21600:1314308846:'
            '8797616454cd88b46baad44abb3c29ac45e467d7"'),
        'data_type': 'chrome:cookie:entry',
        'expiration_time': '2011-11-23T21:48:19.792703+00:00',
        'host': 'www.linkedin.com',
        'httponly': False,
        'persistent': True,
        'url': 'http://www.linkedin.com/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 45)
    self.CheckEventData(event_data, expected_event_values)


class Chrome66CookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Google Chrome 66 Cookies database plugin."""

  def testProcess(self):
    """Tests the Process function on a Chrome cookie database file."""
    plugin = chrome_cookies.Chrome66CookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['Cookies-68.0.3440.106'], plugin)

    # 5 Chrome cookie and 1 cookie plugin.
    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2018-08-14T15:03:45.489599+00:00',
        'cookie_name': '__utma',
        'creation_time': '2018-08-14T15:03:43.650324+00:00',
        'data': '',
        'data_type': 'chrome:cookie:entry',
        'expiration_time': '2020-08-13T15:03:45.000000+00:00',
        'host': 'google.com',
        'httponly': False,
        'persistent': True,
        'url': 'http://google.com/gmail/about/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)

    expected_event_values = {
        'cookie_name': '__utma',
        'data_type': 'cookie:google:analytics:utma',
        'url': 'http://google.com/gmail/about/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
