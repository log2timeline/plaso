#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Tests for the Safari history plist plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import plist as plist_formatter
from plaso.lib import preprocess
from plaso.parsers import plist
from plaso.parsers.plist_plugins import safari
from plaso.parsers.plist_plugins import test_lib


class SafariPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Safari history plist plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = safari.SafariHistoryPlugin(None)
    self._parser = plist.PlistParser(preprocess.PlasoPreprocess(), None)

  def testProcess(self):
    """Tests the Process function."""
    test_file = self._GetTestFilePath(['History.plist'])
    plist_name = 'History.plist'
    events = self._ParsePlistFileWithPlugin(
        self._parser, self._plugin, test_file, plist_name)
    event_objects = self._GetEventObjects(events)

    # 18 entries in timeline.
    self.assertEquals(len(event_objects), 18)

    event_object = event_objects[8]

    # Mon Jul  8 17:31:00 UTC 2013.
    self.assertEquals(event_objects[10].timestamp, 1373304660000000)
    expected_url = u'http://netverslun.sci-mx.is/aminosyrur'
    self.assertEquals(event_object.url, expected_url)

    expected_string = (
        u'Visited: {0:s} (Am\xedn\xf3s\xfdrur ) Visit Count: 1').format(
            expected_url)

    self._TestGetMessageStrings(event_object, expected_string, expected_string)


if __name__ == '__main__':
  unittest.main()
