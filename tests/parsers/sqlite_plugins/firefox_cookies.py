#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugin."""

import unittest

from plaso.formatters import firefox_cookies  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import firefox_cookies

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class FirefoxCookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'firefox_cookies.sqlite'])
  def testProcess(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    plugin_object = firefox_cookies.FirefoxCookiePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'firefox_cookies.sqlite'], plugin_object)

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
    for event in storage_writer.events:
      if event.data_type == u'firefox:cookie:entry':
        test_events.append(event)
      else:
        extra_objects.append(event)

    self.assertEqual(len(test_events), 90 * 3)
    self.assertGreaterEqual(len(extra_objects), 25)

    # Check one greenqloud.com event
    event = test_events[32]
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)
    self.assertEqual(event.host, u's.greenqloud.com')
    self.assertEqual(event.cookie_name, u'__utma')
    self.assertFalse(event.httponly)
    self.assertEqual(event.url, u'http://s.greenqloud.com/')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-10-30 21:56:03')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_message = (
        u'http://s.greenqloud.com/ (__utma) Flags: [HTTP only]: False')
    expected_short_message = u's.greenqloud.com (__utma)'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Check one of the visits to pubmatic.com.
    event = test_events[62]
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_EXPIRATION)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-11-29 21:56:04')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.url, u'http://pubmatic.com/')
    self.assertEqual(event.path, u'/')
    self.assertFalse(event.secure)

    expected_message = (
        u'http://pubmatic.com/ (KRTBCOOKIE_391) Flags: [HTTP only]: False')
    expected_short_message = u'pubmatic.com (KRTBCOOKIE_391)'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
