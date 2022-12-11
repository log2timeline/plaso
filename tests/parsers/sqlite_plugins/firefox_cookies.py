#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugin."""

import unittest

from plaso.parsers.sqlite_plugins import firefox_cookies

from tests.parsers.sqlite_plugins import test_lib


class FirefoxCookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database plugin."""

  def testProcess(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin()
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
        'access_time': '2013-10-30T21:56:03.997686+00:00',
        'cookie_name': '__utma',
        'creation_time': '2013-10-30T21:56:03.992499+00:00',
        'data_type': 'firefox:cookie:entry',
        'expiration_time': '2015-10-30T21:56:03+00:00',
        'host': 's.greenqloud.com',
        'httponly': False,
        'secure': False,
        'url': 'http://s.greenqloud.com/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 13)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
