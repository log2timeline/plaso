#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import firefox_cookies

from tests.parsers.sqlite_plugins import test_lib


class FirefoxCookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database plugin."""

  def testProcess(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin = firefox_cookies.FirefoxCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['firefox_cookies.sqlite'], plugin)

    events = []
    extra_objects = []

    # sqlite> SELECT COUNT(id) FROM moz_cookies;
    # 90
    # Thus the cookie database contains 93 entries:
    #   90 Last Access Time
    #   90 Cookie Expires
    #   90 Creation Time
    #
    # And then in addition the following entries are added due to cookie
    # plugins (TODO filter these out since adding new cookie plugin will
    # change this number and thus affect this test):
    #  15 Last Visited Time
    #   5 Analytics Previous Time
    #   5 Analytics Creation Time
    #
    # In total: 93 * 3 + 15 + 5 + 5 = 304 events.
    for event in storage_writer.GetEvents():
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type == 'firefox:cookie:entry':
        events.append(event)
      else:
        extra_objects.append(event)

    self.assertEqual(len(events), 90 * 3)
    self.assertGreaterEqual(len(extra_objects), 25)

    # Check one greenqloud.com event
    expected_event_values = {
        'cookie_name': '__utma',
        'host': 's.greenqloud.com',
        'httponly': False,
        'timestamp': '2015-10-30 21:56:03.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_EXPIRATION,
        'url': 'http://s.greenqloud.com/'}

    self.CheckEventValues(storage_writer, events[32], expected_event_values)

    expected_message = (
        'http://s.greenqloud.com/ (__utma) Flags: [HTTP only]: False')
    expected_short_message = 's.greenqloud.com (__utma)'

    event_data = self._GetEventDataOfEvent(storage_writer, events[32])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check one of the visits to pubmatic.com.
    expected_event_values = {
        'path': '/',
        'secure': False,
        'timestamp': '2013-11-29 21:56:04.000000',
        'timestamp_desc': definitions.TIME_DESCRIPTION_EXPIRATION,
        'url': 'http://pubmatic.com/'}

    self.CheckEventValues(storage_writer, events[62], expected_event_values)

    expected_message = (
        'http://pubmatic.com/ (KRTBCOOKIE_391) Flags: [HTTP only]: False')
    expected_short_message = 'pubmatic.com (KRTBCOOKIE_391)'

    event_data = self._GetEventDataOfEvent(storage_writer, events[62])
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
