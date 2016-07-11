#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers.plist_plugins import softwareupdate

from tests.parsers.plist_plugins import test_lib


class SoftwareUpdatePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.SoftwareUpdate.plist'

    plugin_object = softwareupdate.SoftwareUpdatePlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin_object, [plist_name], plist_name)

    self.assertEqual(len(storage_writer.events), 2)
    event_object = storage_writer.events[0]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = u'Last Mac OS X 10.9.1 (13B42) full update.'
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'// {0:s}'.format(expected_desc)
    self._TestGetMessageStrings(
        event_object, expected_string, expected_string)

    event_object = storage_writer.events[1]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = (
        u'Last Mac OS 10.9.1 (13B42) partially '
        u'update, pending 1: RAWCameraUpdate5.03(031-2664).')
    self.assertEqual(event_object.desc, expected_desc)


if __name__ == '__main__':
  unittest.main()
