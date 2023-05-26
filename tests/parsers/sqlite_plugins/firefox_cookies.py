#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugins."""

import unittest

from plaso.parsers.sqlite_plugins import firefox_cookies

from tests.parsers.sqlite_plugins import test_lib


class Firefox2CookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database schema version 2."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = firefox_cookies.FirefoxCookie2Plugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_2_cookies.sqlite'], plugin)

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


class Firefox10CookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database version 10 plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plugin = firefox_cookies.FirefoxCookie10Plugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_10_cookies.sqlite'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 13)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'access_time': '2023-05-05T16:00:44.811189+00:00',
        'cookie_name': 'WMF-Last-Access',
        'creation_time': '2023-05-05T16:00:44.811189+00:00',
        'data_type': 'firefox:cookie:entry',
        'expiration_time': '2023-06-06T12:00:00+00:00',
        'host': 'en.wikipedia.org',
        'httponly': True,
        'secure': True,
        'url': 'https://en.wikipedia.org/'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 4)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
