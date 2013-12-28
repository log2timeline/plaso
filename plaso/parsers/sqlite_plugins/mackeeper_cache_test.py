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
"""Tests for the MacKeeper Cache parser."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import mackeeper_cache as cache_formatter
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import interface
from plaso.parsers.sqlite_plugins import mackeeper_cache
from plaso.pvfs import utils

import pytz


class MacKeeperCachePluginTest(unittest.TestCase):
  """Tests for the MacKeeper Cache parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = mackeeper_cache.MacKeeperCachePlugin(pre_obj)

  def testParseFile(self):
    """Read a Chrome History file and run a few tests."""
    test_file = os.path.join('test_data', 'mackeeper_cache.db')

    events = None
    file_entry = utils.OpenOSFileEntry(test_file)
    with interface.SQLiteDatabase(file_entry) as database:
      generator = self.test_parser.Process(database)
      self.assertTrue(generator)
      events = list(generator)

    # The cache file contains 198 entries.
    self.assertEquals(len(events), 198)

    # Test the event specific formatter.
    chat_event = events[41]

    # 2013-07-12T19:30:31+00:00.
    self.assertEquals(chat_event.timestamp, 1373657431000000)

    msg, _ = eventdata.EventFormatterManager.GetMessageStrings(
         chat_event)

    expected_msg = (
        'Chat Outgoing Message : I have received your system scan report and '
        'I will start analyzing it right now. [ URL: http://support.kromtech.'
        'net/chat/listen/12828340738351e0593f987450z40787/?client-id=51e0593f'
        'a1a24468673655&callback=jQuery183013571173651143909_1373657420912&_='
        '1373657423647 Event ID: 16059074 Room: '
        '12828340738351e0593f987450z40787 ]')

    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
