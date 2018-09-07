#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the Kik messenger plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import kik_ios as _  # pylint: disable=unused-import
from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import kik_ios

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class KikMessageTest(test_lib.SQLitePluginTestCase):
  """Tests for the Kik message database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['kik_ios.sqlite'])
  def testProcess(self):
    """Test the Process function on a Kik messenger kik.sqlite file."""
    plugin = kik_ios.KikIOSPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['kik_ios.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_errors, 0)
    self.assertEqual(storage_writer.number_of_events, 60)

    events = list(storage_writer.GetEvents())

    # Check the second message sent.
    event = events[1]

    self.CheckTimestamp(event.timestamp, '2015-06-29 12:26:11.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)

    self.assertEqual(event.username, 'ken.doh')
    self.assertEqual(event.displayname, 'Ken Doh')
    self.assertEqual(event.body, 'Hello')

    expected_message = (
        'Username: ken.doh '
        'Displayname: Ken Doh '
        'Status: read after offline '
        'Type: sent '
        'Message: Hello')
    expected_short_message = 'Hello'
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
