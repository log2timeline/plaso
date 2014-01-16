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
"""Tests for the MacKeeper Cache database plugin."""

import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mackeeper_cache as mackeeper_cache_formatter
from plaso.lib import event
from plaso.parsers.sqlite_plugins import mackeeper_cache
from plaso.parsers.sqlite_plugins import test_lib


class MacKeeperCachePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the MacKeeper Cache database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = event.PreprocessObject()
    self._plugin = mackeeper_cache.MacKeeperCachePlugin(pre_obj)

  def testProcess(self):
    """Tests the Process function on a MacKeeper Cache database file."""
    test_file = self._GetTestFilePath(['mackeeper_cache.db'])
    event_generator = self._ParseDatabaseFileWithPlugin(self._plugin, test_file)
    event_objects = self._GetEventObjects(event_generator)

    # The cache file contains 198 entries.
    self.assertEquals(len(event_objects), 198)

    event_object = event_objects[41]

    # 2013-07-12T19:30:31+00:00.
    self.assertEquals(event_object.timestamp, 1373657431000000)

    expected_msg = (
        u'Chat Outgoing Message : I have received your system scan report and '
        u'I will start analyzing it right now. [ URL: http://support.kromtech.'
        u'net/chat/listen/12828340738351e0593f987450z40787/?client-id=51e0593f'
        u'a1a24468673655&callback=jQuery183013571173651143909_1373657420912&_='
        u'1373657423647 Event ID: 16059074 Room: '
        u'12828340738351e0593f987450z40787 ]')

    expected_short = (
        u'I have received your system scan report and I will start analyzing '
        u'it right now.')

    self._TestGetMessageStrings(event_object, expected_msg, expected_short)


if __name__ == '__main__':
  unittest.main()
