#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Zeitgeist activity database plugin."""

import unittest

from plaso.formatters import zeitgeist  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import zeitgeist

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class ZeitgeistPluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Zeitgeist activity database plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'activity.sqlite'])
  def testProcess(self):
    """Tests the Process function."""
    plugin_object = zeitgeist.ZeitgeistPlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        [u'activity.sqlite'], plugin_object)

    # The sqlite database contains 44 events.
    self.assertEqual(len(storage_writer.events), 44)

    # Check the first event.
    event_object = storage_writer.events[0]

    expected_subject_uri = u'application://rhythmbox.desktop'
    self.assertEqual(event_object.subject_uri, expected_subject_uri)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-10-22 08:53:19.477')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    expected_msg = u'application://rhythmbox.desktop'
    self._TestGetMessageStrings(event_object, expected_msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
