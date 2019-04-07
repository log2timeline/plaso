#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the MacOS Knowledge C db."""

from __future__ import unicode_literals

import unittest

from plaso.lib import definitions
from plaso.parsers.sqlite_plugins import mac_knowledgec

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class MacKnowledgecTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacOS Knowledge C db."""

  def testProcess(self):
    """Tests the Process function on a MacOS KnowledgeC db."""

    plugin = mac_knowledgec.MacKnowledgeCPlugin()
    storage_writer_10_13 = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.13.db'], plugin)
    storage_writer_10_14 = self._ParseDatabaseFileWithPlugin(
        ['mac_knowledgec-10.14.db'], plugin)

    # Mac oS 10.13 version
    self.assertEqual(51, storage_writer_10_13.number_of_events)
    events = list(storage_writer_10_13.GetEvents())
    event = events[0]
    self.CheckTimestamp(event.timestamp, '2019-02-10 16:59:58.860665')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.action, '/app/inFocus')
    self.assertEqual(event.bundle_id, 'com.apple.Installer-Progress')
    expected_message = (
        'Application {} executed during {} seconds'.format(
            event.bundle_id, event.usage_in_seconds))
    expected_short_message = ('Application {}'.format(event.bundle_id))
    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    # Mac oS 10.14 version
    self.assertEqual(231, storage_writer_10_14.number_of_events)
    events = list(storage_writer_10_14.GetEvents())

    event = events[225]
    self.CheckTimestamp(event.timestamp, '2019-05-08 13:57:30.668998')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_CREATION)
    self.assertEqual(event.action, '/app/usage')
    self.assertEqual(event.bundle_id, 'com.apple.Terminal')
    expected_message = (
        'Application {} executed during {} seconds'.format(
            event.bundle_id, event.usage_in_seconds))
    expected_short_message = ('Application {}'.format(event.bundle_id))

    event = events[212]
    self.CheckTimestamp(event.timestamp, '2019-05-08 13:57:20.000000')
    self.assertEqual(
        event.timestamp_desc, definitions.TIME_DESCRIPTION_END)
    self.assertEqual(event.uri, 'https://www.instagram.com/')
    self.assertEqual(event.uri_title, 'Instagram')
    expected_message = (
        'Safari open uri {} with title {} and was visited during {} seconds'.format(
            event.uri, event.uri_title, event.usage_in_seconds))
    expected_short_message = ('Safari open uri {}'.format(event.uri))
    self._TestGetMessageStrings(event, expected_message, expected_short_message)


if __name__ == '__main__':
  unittest.main()
