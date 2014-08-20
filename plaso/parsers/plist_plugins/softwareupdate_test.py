#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
    test_file = self._GetTestFilePath([plist_name])
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    self.assertEquals(len(event_objects), 2)
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
