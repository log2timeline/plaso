#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the launchd plist plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import launchd

from tests.parsers.plist_plugins import test_lib


class LaunchdPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the launchd plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = 'launchd.plist'

    plugin = launchd.LaunchdPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(plugin, [plist_name],
                                                    plist_name)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 1)

    events = list(storage_writer.GetSortedEvents())
    event = events[0]
    self.assertEqual(event.timestamp, 0)
    event_data = self._GetEventDataOfEvent(storage_writer, event)
    self.assertEqual(event_data.key, 'launchdServiceConfig')
    self.assertEqual(event_data.root, '/')
    expected_desc = ('Launchd service config com.foobar.test points to /Test '
                     '--flag arg1 with user:nobody group:nobody')
    self.assertEqual(event_data.desc, expected_desc)


if __name__ == '__main__':
  unittest.main()
