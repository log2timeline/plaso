#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.parsers.plist_plugins import softwareupdate

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class SoftwareUpdatePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'com.apple.SoftwareUpdate.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.SoftwareUpdate.plist'

    plugin_object = softwareupdate.SoftwareUpdatePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = self._GetSortedEvents(storage_writer.events)

    event_object = events[0]

    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = (
        u'Last Mac OS 10.9.1 (13B42) partially '
        u'update, pending 1: RAWCameraUpdate5.03(031-2664).')
    self.assertEqual(event_object.desc, expected_desc)

    event_object = events[1]

    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = u'Last Mac OS X 10.9.1 (13B42) full update.'
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'// {0:s}'.format(expected_desc)
    self._TestGetMessageStrings(
        event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
