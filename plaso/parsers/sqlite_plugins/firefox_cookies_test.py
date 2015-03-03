#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Firefox cookie database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import firefox_cookies as firefox_cookies_formatter
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import firefox_cookies
from plaso.parsers.sqlite_plugins import test_lib


class FirefoxCookiesPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Firefox cookie database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = firefox_cookies.FirefoxCookiePlugin()

  def testProcess(self):
    """Tests the Process function on a Firefox 29 cookie database file."""
    test_file = self._GetTestFilePath([u'firefox_cookies.sqlite'])
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file)

    event_objects = []
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
    for event_object in self._GetEventObjectsFromQueue(event_queue_consumer):
      if isinstance(event_object, firefox_cookies.FirefoxCookieEvent):
        event_objects.append(event_object)
      else:
        extra_objects.append(event_object)

    self.assertEqual(len(event_objects), 90 * 3)
    self.assertGreaterEqual(len(extra_objects), 25)

    # Check one greenqloud.com event
    event_object = event_objects[32]
    self.assertEquals(event_object.timestamp_desc, u'Cookie Expires')
    self.assertEquals(event_object.host, u's.greenqloud.com')
    self.assertEquals(event_object.cookie_name, u'__utma')
    self.assertFalse(event_object.httponly)
    self.assertEqual(event_object.url, u'http://s.greenqloud.com/')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2015-10-30 21:56:03')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    expected_msg = (
        u'http://s.greenqloud.com/ (__utma) Flags: [HTTP only]: False')
    expected_short = u's.greenqloud.com (__utma)'
    self._TestGetMessageStrings(event_object, expected_msg, expected_short)

    # Check one of the visits to pubmatic.com.
    event_object = event_objects[62]
    self.assertEqual(
        event_object.timestamp_desc, u'Cookie Expires')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        U'2013-11-29 21:56:04')
    self.assertEquals(event_object.timestamp, expected_timestamp)

    self.assertEqual(event_object.url, u'http://pubmatic.com/')
    self.assertEqual(event_object.path, u'/')
    self.assertFalse(event_object.secure)

    expected_msg = (
        u'http://pubmatic.com/ (KRTBCOOKIE_391) Flags: [HTTP only]: False')
    self._TestGetMessageStrings(
        event_object, expected_msg, u'pubmatic.com (KRTBCOOKIE_391)')


if __name__ == '__main__':
  unittest.main()
