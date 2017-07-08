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

    plugin = softwareupdate.SoftwareUpdatePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 2)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    self.assertEqual(event.key, u'')
    self.assertEqual(event.root, u'/')
    expected_desc = (
        u'Last Mac OS 10.9.1 (13B42) partially '
        u'update, pending 1: RAWCameraUpdate5.03(031-2664).')
    self.assertEqual(event.desc, expected_desc)

    event = events[1]

    self.assertEqual(event.key, u'')
    self.assertEqual(event.root, u'/')
    expected_desc = u'Last Mac OS X 10.9.1 (13B42) full update.'
    self.assertEqual(event.desc, expected_desc)
    expected_string = u'// {0:s}'.format(expected_desc)
    self._TestGetMessageStrings(event, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
