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
"""Tests for the Skype main.db history parser."""

import os
import unittest

# pylint: disable-msg=unused-import
from plaso.formatters import skype as skype_formatter
from plaso.lib import preprocess
from plaso.parsers.sqlite_plugins import interface
from plaso.parsers.sqlite_plugins import skype
from plaso.pvfs import utils

import pytz


class SkypePluginTest(unittest.TestCase):
  """Tests for the Skye main.db history parser."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    pre_obj = preprocess.PlasoPreprocess()
    pre_obj.zone = pytz.UTC

    self.test_parser = skype.SkypePlugin(pre_obj)

  def testParseFile(self):
    """
      Read a skype history file and run a few tests.

      The History file contains 24 events:
          4 call events
          4 transfers file events
          1 sms events
         15 chat events

      Events used:
        id = 16 -> SMS
        id = 22 -> Call
        id = 18 -> File
        id =  1 -> Chat
        id = 14 -> ChatRoom
    """
    test_file = os.path.join('test_data', 'skype_main.db')

    events = None
    file_entry = utils.OpenOSFileEntry(test_file)
    with interface.SQLiteDatabase(file_entry) as database:
      generator = self.test_parser.Process(database)
      self.assertTrue(generator)
      events = list(generator)

    calls = 0
    files = 0
    sms = 0
    chats = 0
    for event in events:
      if event.data_type == 'skype:event:call':
        calls = calls + 1
      if event.data_type == 'skype:event:transferfile':
        files = files + 1
      if event.data_type == 'skype:event:sms':
        sms = sms + 1
      if event.data_type == 'skype:event:chat':
        chats = chats + 1

    self.assertEquals(len(events), 24)
    self.assertEquals(files, 4)
    self.assertEquals(sms, 1)
    self.assertEquals(chats, 15)
    self.assertEquals(calls, 3)

    event_sms = events[16]
    event_call = events[22]
    event_file = events[18]
    event_chat = events[1]
    event_chat_room = events[14]

    # date -u -d"Jul 01, 2013 22:14:22" +"%s.%N"
    timestamp = 1372716862 * 1000000
    self.assertEquals(event_sms.timestamp, timestamp)
    text_sms = (u'If you want I can copy '
                u'some documents for you, '
                u'if you can pay it... ;)')
    self.assertEquals(event_sms.text, text_sms)
    number = u'+34123456789'
    self.assertEquals(event_sms.number, number)

    # date -u -d"Oct 24, 2013 21:49:35" +"%s.%N"
    timestamp = 1382651375 * 1000000
    self.assertEquals(event_file.timestamp, timestamp)
    action_type = u'GETSOLICITUDE'
    self.assertEquals(event_file.action_type, action_type)
    source = u'gen.beringer <Gen Beringer>'
    self.assertEquals(event_file.source, source)
    destination = u'european.bbq.competitor <European BBQ>'
    self.assertEquals(event_file.destination, destination)
    transferred_filename = u'secret-project.pdf'
    self.assertEquals(event_file.transferred_filename, transferred_filename)
    filepath = u'/Users/gberinger/Desktop/secret-project.pdf'
    self.assertEquals(event_file.transferred_filepath, filepath)
    self.assertEquals(event_file.transferred_filesize, 69986)

    # date -u -d"Jul 30, 2013 21:27:11" +"%s.%N"
    timestamp = 1375219631 * 1000000
    self.assertEquals(event_chat.timestamp, timestamp)
    title = u'European Competitor | need to know if you got it..'
    self.assertEquals(event_chat.title, title)
    expected_msg = u'need to know if you got it this time.'
    self.assertEquals(event_chat.text, expected_msg)
    from_account = u'Gen Beringer <gen.beringer>'
    self.assertEquals(event_chat.from_account, from_account)
    self.assertEquals(event_chat.to_account, u'european.bbq.competitor')

    # date -u -d"Oct 27, 2013 15:29:19" +"%s.%N"
    timestamp = 1382887759 * 1000000
    self.assertEquals(event_chat_room.timestamp, timestamp)
    title = u'European Competitor, Echo123'
    self.assertEquals(event_chat_room.title, title)
    expected_msg = u'He is our new employee'
    self.assertEquals(event_chat_room.text, expected_msg)
    from_account = u'European Competitor <european.bbq.competitor>'
    self.assertEquals(event_chat_room.from_account, from_account)
    to_account = u'gen.beringer, echo123'
    self.assertEquals(event_chat_room.to_account, to_account)

    # date -u -d"Jul 01, 2013 22:12:17" +"%s.%N"
    timestamp = 1372716737 * 1000000
    self.assertEquals(event_call.timestamp, timestamp)
    self.assertEquals(event_call.dst_call, u'european.bbq.competitor')
    self.assertEquals(event_call.src_call, u'gen.beringer')
    self.assertEquals(event_call.user_start_call, False)
    self.assertEquals(event_call.video_conference, False)


if __name__ == '__main__':
  unittest.main()
