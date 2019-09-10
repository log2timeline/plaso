#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Skype main.db history database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import skype as _  # pylint: disable=unused-import
from plaso.parsers.sqlite_plugins import skype

from tests.parsers.sqlite_plugins import test_lib


class SkypePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Skype main.db history database plugin."""

  def testProcess(self):
    """Tests the Process function on a Skype History database file.

    The History file contains 24 events:
      3 call events
      4 transfers file events
      1 sms event
      1 account event
      15 chat events

    Events used:
      id = 16 -> SMS
      id = 22 -> Call
      id = 18 -> File
      id =  1 -> Chat
      id = 14 -> ChatRoom
    """
    plugin = skype.SkypePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['skype_main.db'], plugin)

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 24)

    events = list(storage_writer.GetEvents())

    number_of_calls = 0
    number_of_files = 0
    number_of_sms = 0
    number_of_chats = 0
    number_of_account_events = 0
    for event in events:
      event_data = self._GetEventDataOfEvent(storage_writer, event)
      if event_data.data_type == 'skype:event:call':
        number_of_calls += 1
      if event_data.data_type == 'skype:event:transferfile':
        number_of_files += 1
      if event_data.data_type == 'skype:event:sms':
        number_of_sms += 1
      if event_data.data_type == 'skype:event:chat':
        number_of_chats += 1
      if event_data.data_type == 'skype:event:account':
        number_of_account_events += 1

    self.assertEqual(number_of_files, 4)
    self.assertEqual(number_of_sms, 1)
    self.assertEqual(number_of_chats, 15)
    self.assertEqual(number_of_calls, 3)

    # Test cache processing and format strings.
    event = events[17]

    event_data = self._GetEventDataOfEvent(storage_writer, event)

    expected_message = (
        'Source: gen.beringer <Gen Beringer> Destination: '
        'european.bbq.competitor <European BBQ> File: secret-project.pdf '
        '[SENDSOLICITUDE]')
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(
        event_data, expected_message, expected_short_message)

    sms_event = events[16]

    self.CheckTimestamp(sms_event.timestamp, '2013-07-01 22:14:22.000000')

    sms_event_data = self._GetEventDataOfEvent(storage_writer, sms_event)
    text_sms = (
        'If you want I can copy '
        'some documents for you, '
        'if you can pay it... ;)')
    self.assertEqual(sms_event_data.text, text_sms)
    self.assertEqual(sms_event_data.number, '+34123456789')

    file_event = events[18]

    self.CheckTimestamp(file_event.timestamp, '2013-10-24 21:49:35.000000')

    file_event_data = self._GetEventDataOfEvent(storage_writer, file_event)
    self.assertEqual(file_event_data.action_type, 'GETSOLICITUDE')
    self.assertEqual(
        file_event_data.source, 'gen.beringer <Gen Beringer>')
    self.assertEqual(
        file_event_data.destination, 'european.bbq.competitor <European BBQ>')
    self.assertEqual(
        file_event_data.transferred_filename, 'secret-project.pdf')
    self.assertEqual(
        file_event_data.transferred_filepath,
        '/Users/gberinger/Desktop/secret-project.pdf')
    self.assertEqual(file_event_data.transferred_filesize, 69986)

    chat_event = events[1]

    self.CheckTimestamp(chat_event.timestamp, '2013-07-30 21:27:11.000000')

    chat_event_data = self._GetEventDataOfEvent(storage_writer, chat_event)
    self.assertEqual(
        chat_event_data.title,
        'European Competitor | need to know if you got it..')
    self.assertEqual(
        chat_event_data.text, 'need to know if you got it this time.')
    self.assertEqual(
        chat_event_data.from_account, 'Gen Beringer <gen.beringer>')
    self.assertEqual(chat_event_data.to_account, 'european.bbq.competitor')

    chat_room_event = events[14]

    self.CheckTimestamp(chat_room_event.timestamp, '2013-10-27 15:29:19.000000')

    chat_room_event_data = self._GetEventDataOfEvent(
        storage_writer, chat_room_event)
    self.assertEqual(chat_room_event_data.title, 'European Competitor, Echo123')
    self.assertEqual(chat_room_event_data.text, 'He is our new employee')
    self.assertEqual(
        chat_room_event_data.from_account,
        'European Competitor <european.bbq.competitor>')
    self.assertEqual(chat_room_event_data.to_account, 'gen.beringer, echo123')

    call_event = events[22]

    self.CheckTimestamp(call_event.timestamp, '2013-07-01 22:12:17.000000')

    call_event_data = self._GetEventDataOfEvent(storage_writer, call_event)
    self.assertEqual(call_event_data.dst_call, 'european.bbq.competitor')
    self.assertEqual(call_event_data.src_call, 'gen.beringer')
    self.assertEqual(call_event_data.user_start_call, False)
    self.assertEqual(call_event_data.video_conference, False)


if __name__ == '__main__':
  unittest.main()
