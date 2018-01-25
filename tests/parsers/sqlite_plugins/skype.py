#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Skype main.db history database plugin."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import skype as _  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import skype

from tests import test_lib as shared_test_lib
from tests.parsers.sqlite_plugins import test_lib


class SkypePluginTest(test_lib.SQLitePluginTestCase):
  """Tests for the Skype main.db history database plugin."""

  @shared_test_lib.skipUnlessHasTestFile(['skype_main.db'])
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
    plugin = skype.SkypePlugin()
    storage_writer = self._ParseDatabaseFileWithPlugin(
        ['skype_main.db'], plugin)

    self.assertEqual(storage_writer.number_of_events, 24)

    events = list(storage_writer.GetEvents())

    number_of_calls = 0
    number_of_files = 0
    number_of_sms = 0
    number_of_chats = 0
    for event in events:
      if event.data_type == 'skype:event:call':
        number_of_calls += 1
      if event.data_type == 'skype:event:transferfile':
        number_of_files += 1
      if event.data_type == 'skype:event:sms':
        number_of_sms += 1
      if event.data_type == 'skype:event:chat':
        number_of_chats += 1

    self.assertEqual(number_of_files, 4)
    self.assertEqual(number_of_sms, 1)
    self.assertEqual(number_of_chats, 15)
    self.assertEqual(number_of_calls, 3)

    # TODO: Split this up into separate functions for testing each type of
    # event, e.g. testSMS, etc.
    sms_event = events[16]
    call_event = events[22]
    event_file = events[18]
    chat_event = events[1]
    chat_room_event = events[14]

    # Test cache processing and format strings.
    event = events[17]

    expected_message = (
        'Source: gen.beringer <Gen Beringer> Destination: '
        'european.bbq.competitor <European BBQ> File: secret-project.pdf '
        '[SENDSOLICITUDE]')
    expected_short_message = '{0:s}...'.format(expected_message[:77])

    self._TestGetMessageStrings(event, expected_message, expected_short_message)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-01 22:14:22')
    self.assertEqual(sms_event.timestamp, expected_timestamp)

    text_sms = (
        'If you want I can copy '
        'some documents for you, '
        'if you can pay it... ;)')
    self.assertEqual(sms_event.text, text_sms)

    self.assertEqual(sms_event.number, '+34123456789')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-10-24 21:49:35')
    self.assertEqual(event_file.timestamp, expected_timestamp)

    action_type = 'GETSOLICITUDE'
    self.assertEqual(event_file.action_type, action_type)
    source = 'gen.beringer <Gen Beringer>'
    self.assertEqual(event_file.source, source)
    destination = 'european.bbq.competitor <European BBQ>'
    self.assertEqual(event_file.destination, destination)
    transferred_filename = 'secret-project.pdf'
    self.assertEqual(event_file.transferred_filename, transferred_filename)
    filepath = '/Users/gberinger/Desktop/secret-project.pdf'
    self.assertEqual(event_file.transferred_filepath, filepath)
    self.assertEqual(event_file.transferred_filesize, 69986)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-30 21:27:11')
    self.assertEqual(chat_event.timestamp, expected_timestamp)

    title = 'European Competitor | need to know if you got it..'
    self.assertEqual(chat_event.title, title)
    expected_message = 'need to know if you got it this time.'
    self.assertEqual(chat_event.text, expected_message)
    from_account = 'Gen Beringer <gen.beringer>'
    self.assertEqual(chat_event.from_account, from_account)
    self.assertEqual(chat_event.to_account, 'european.bbq.competitor')

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-10-27 15:29:19')
    self.assertEqual(chat_room_event.timestamp, expected_timestamp)

    title = 'European Competitor, Echo123'
    self.assertEqual(chat_room_event.title, title)
    expected_message = 'He is our new employee'
    self.assertEqual(chat_room_event.text, expected_message)
    from_account = 'European Competitor <european.bbq.competitor>'
    self.assertEqual(chat_room_event.from_account, from_account)
    to_account = 'gen.beringer, echo123'
    self.assertEqual(chat_room_event.to_account, to_account)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        '2013-07-01 22:12:17')
    self.assertEqual(call_event.timestamp, expected_timestamp)

    self.assertEqual(call_event.dst_call, 'european.bbq.competitor')
    self.assertEqual(call_event.src_call, 'gen.beringer')
    self.assertEqual(call_event.user_start_call, False)
    self.assertEqual(call_event.video_conference, False)


if __name__ == '__main__':
  unittest.main()
