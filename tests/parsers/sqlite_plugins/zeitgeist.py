#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import zeitgeist as _  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import zeitgeist

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ZeitgeistActivityDatabasePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['activity.sqlite'])
  def testProcess(self):
    """Tests the Process function."""
    plugin = zeitgeist.ZeitgeistActivityDatabasePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['activity.sqlite'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 44)

    events = list(storage_writer.GetEvents())

    # Check the first event.
    event = events[0]

    self.CheckTimestamp(event.timestamp, '2013-10-22 08:53:19.477000')

    self.assertEqual(event.subject_uri, 'application://rhythmbox.desktop')

    expected_message = 'application://rhythmbox.desktop'
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
