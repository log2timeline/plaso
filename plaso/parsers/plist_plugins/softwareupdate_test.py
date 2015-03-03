#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Software Update plist plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.parsers import plist
from plaso.parsers.plist_plugins import softwareupdate
from plaso.parsers.plist_plugins import test_lib


class SoftwareUpdatePluginTest(test_lib.PlistPluginTestCase):
  """Tests for the SoftwareUpdate plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = softwareupdate.SoftwareUpdatePlugin()
    self._parser = plist.PlistParser()

  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'com.apple.SoftwareUpdate.plist'
    event_queue_consumer = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, [plist_name], plist_name)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 2)
    event_object = event_objects[0]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = u'Last Mac OS X 10.9.1 (13B42) full update.'
    self.assertEqual(event_object.desc, expected_desc)
    expected_string = u'// {}'.format(expected_desc)
    self._TestGetMessageStrings(
        event_object, expected_string, expected_string)

    event_object = event_objects[1]
    self.assertEqual(event_object.key, u'')
    self.assertEqual(event_object.root, u'/')
    expected_desc = (
        u'Last Mac OS 10.9.1 (13B42) partially '
        u'update, pending 1: RAWCameraUpdate5.03(031-2664).')
    self.assertEqual(event_object.desc, expected_desc)


if __name__ == '__main__':
  unittest.main()
