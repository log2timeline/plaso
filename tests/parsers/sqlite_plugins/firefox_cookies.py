#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import firefox_cookies as _  # pylint: disable=unused-import
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

    test_events = []
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
        test_events.append(event)
      else:
        extra_objects.append(event)

    self.assertEqual(len(test_events), 90 * 3)
    self.assertGreaterEqual(len(extra_objects), 25)

    # Check one greenqloud.com event
    event = test_events[32]

    self.CheckTimestamp(event.timestamp, '2015-10-30 21:56:03.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.host, 's.greenqloud.com')
    self.assertEqual(event_data.cookie_name, '__utma')
    self.assertFalse(event_data.httponly)
    self.assertEqual(event_data.url, 'http://s.greenqloud.com/')

    expected_message = (
        'http://s.greenqloud.com/ (__utma) Flags: [HTTP only]: False')
    expected_short_message = 's.greenqloud.com (__utma)'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    # Check one of the visits to pubmatic.com.
    event = test_events[62]

    self.CheckTimestamp(event.timestamp, '2013-11-29 21:56:04.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)

    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.url, 'http://pubmatic.com/')
    self.assertEqual(event_data.path, '/')
    self.assertFalse(event_data.secure)

    expected_message = (
        'http://pubmatic.com/ (KRTBCOOKIE_391) Flags: [HTTP only]: False')
    expected_short_message = 'pubmatic.com (KRTBCOOKIE_391)'
    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
