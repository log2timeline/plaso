#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

import unittest

from plaso.formatters import zeitgeist  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import zeitgeist

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ZeitgeistActivityDatabasePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'activity.sqlite'])
  def testProcess(self):
    """Tests the Process function."""
    plugin_object = zeitgeist.ZeitgeistActivityDatabasePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'activity.sqlite'], plugin_object)

    # The sqlite database contains 44 events.
    self.assertEqual(len(storage_writer.events), 44)

    # Check the first event.
    event = storage_writer.events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-22 08:53:19.477')
    self.assertEqual(event.timestamp, expected_timestamp)

    expected_subject_uri = u'application://rhythmbox.desktop'
    self.assertEqual(event.subject_uri, expected_subject_uri)

    expected_message = u'application://rhythmbox.desktop'
    self._TestGetMessageStrings(event, expected_message, expected_message)


if __name__ == '__main__':
  unittest.main()
