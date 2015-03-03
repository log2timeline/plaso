#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Skype main.db history database plugin."""

import unittest

# pylint: disable=unused-import
from plaso.formatters import skype as skype_formatter
from plaso.lib import timelib_test
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import skype
from plaso.parsers.sqlite_plugins import test_lib


class SkypePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Skype main.db history database plugin."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._plugin = skype.SkypePlugin()

  def testProcess(self):
    """Tests the Process function on a Skype History database file.

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
    test_file = self._GetTestFilePath(['skype_main.db'])
    cache = sqlite.SQLiteCache()
    event_queue_consumer = self._ParseDatabaseFileWithPlugin(
        self._plugin, test_file, cache)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    calls = 0
    files = 0
    sms = 0
    chats = 0
    for event_object in event_objects:
      if event_object.data_type == 'skype:event:call':
        calls += 1
      if event_object.data_type == 'skype:event:transferfile':
        files += 1
      if event_object.data_type == 'skype:event:sms':
        sms += 1
      if event_object.data_type == 'skype:event:chat':
        chats += 1

    self.assertEqual(len(event_objects), 24)
    self.assertEqual(files, 4)
    self.assertEqual(sms, 1)
    self.assertEqual(chats, 15)
    self.assertEqual(calls, 3)

    # TODO: Split this up into separate functions for testing each type of
    # event, eg: testSMS, etc.
    sms_event_object = event_objects[16]
    call_event_object = event_objects[22]
    event_file = event_objects[18]
    chat_event_object = event_objects[1]
    chat_room_event_object = event_objects[14]

    # Test cache processing and format strings.
    expected_msg = (
        u'Source: gen.beringer <Gen Beringer> Destination: '
        u'european.bbq.competitor <European BBQ> File: secret-project.pdf '
        u'[SENDSOLICITUDE]')

    self._TestGetMessageStrings(
        event_objects[17], expected_msg, expected_msg[0:77] + '...')

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-01 22:14:22')
    self.assertEqual(sms_event_object.timestamp, expected_timestamp)
    text_sms = (u'If you want I can copy '
                u'some documents for you, '
                u'if you can pay it... ;)')
    self.assertEqual(sms_event_object.text, text_sms)
    number = u'+34123456789'
    self.assertEqual(sms_event_object.number, number)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-24 21:49:35')
    self.assertEqual(event_file.timestamp, expected_timestamp)

    action_type = u'GETSOLICITUDE'
    self.assertEqual(event_file.action_type, action_type)
    source = u'gen.beringer <Gen Beringer>'
    self.assertEqual(event_file.source, source)
    destination = u'european.bbq.competitor <European BBQ>'
    self.assertEqual(event_file.destination, destination)
    transferred_filename = u'secret-project.pdf'
    self.assertEqual(event_file.transferred_filename, transferred_filename)
    filepath = u'/Users/gberinger/Desktop/secret-project.pdf'
    self.assertEqual(event_file.transferred_filepath, filepath)
    self.assertEqual(event_file.transferred_filesize, 69986)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-30 21:27:11')
    self.assertEqual(chat_event_object.timestamp, expected_timestamp)

    title = u'European Competitor | need to know if you got it..'
    self.assertEqual(chat_event_object.title, title)
    expected_msg = u'need to know if you got it this time.'
    self.assertEqual(chat_event_object.text, expected_msg)
    from_account = u'Gen Beringer <gen.beringer>'
    self.assertEqual(chat_event_object.from_account, from_account)
    self.assertEqual(chat_event_object.to_account, u'european.bbq.competitor')

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-10-27 15:29:19')
    self.assertEqual(chat_room_event_object.timestamp, expected_timestamp)

    title = u'European Competitor, Echo123'
    self.assertEqual(chat_room_event_object.title, title)
    expected_msg = u'He is our new employee'
    self.assertEqual(chat_room_event_object.text, expected_msg)
    from_account = u'European Competitor <european.bbq.competitor>'
    self.assertEqual(chat_room_event_object.from_account, from_account)
    to_account = u'gen.beringer, echo123'
    self.assertEqual(chat_room_event_object.to_account, to_account)

    expected_timestamp = timelib_test.CopyStringToTimestamp(
        '2013-07-01 22:12:17')
    self.assertEqual(call_event_object.timestamp, expected_timestamp)

    self.assertEqual(call_event_object.dst_call, u'european.bbq.competitor')
    self.assertEqual(call_event_object.src_call, u'gen.beringer')
    self.assertEqual(call_event_object.user_start_call, False)
    self.assertEqual(call_event_object.video_conference, False)


if __name__ == '__main__':
  unittest.main()
