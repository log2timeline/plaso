#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Skype main.db history database plugin."""

import unittest

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

    number_of_events = storage_writer.GetNumberOfAttributeContainers('event')
    self.assertEqual(number_of_events, 24)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

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

    # Test transfer file event.
    expected_event_values = {
        'action_type': 'SENDSOLICITUDE',
        'data_type': 'skype:event:transferfile',
        'date_time': '2013-10-24 21:49:32',
        'destination': 'european.bbq.competitor <European BBQ>',
        'source': 'gen.beringer <Gen Beringer>',
        'transferred_filename': 'secret-project.pdf'}

    self.CheckEventValues(storage_writer, events[17], expected_event_values)

    # Test SMS event.
    expected_event_values = {
        'data_type': 'skype:event:sms',
        'date_time': '2013-07-01 22:14:22',
        'number': '+34123456789',
        'text': (
            'If you want I can copy some documents for you, if you can pay '
            'it... ;)')}

    self.CheckEventValues(storage_writer, events[16], expected_event_values)

    # Test file event.
    expected_event_values = {
        'action_type': 'GETSOLICITUDE',
        'data_type': 'skype:event:transferfile',
        'date_time': '2013-10-24 21:49:35',
        'destination': 'european.bbq.competitor <European BBQ>',
        'source': 'gen.beringer <Gen Beringer>',
        'transferred_filename': 'secret-project.pdf',
        'transferred_filepath': '/Users/gberinger/Desktop/secret-project.pdf',
        'transferred_filesize': 69986}

    self.CheckEventValues(storage_writer, events[18], expected_event_values)

    # Test chat event.
    expected_event_values = {
        'data_type': 'skype:event:chat',
        'date_time': '2013-07-30 21:27:11',
        'from_account': 'Gen Beringer <gen.beringer>',
        'text': 'need to know if you got it this time.',
        'title': 'European Competitor | need to know if you got it..',
        'to_account': 'european.bbq.competitor'}

    self.CheckEventValues(storage_writer, events[1], expected_event_values)

    # Test chat room event.
    expected_event_values = {
        'data_type': 'skype:event:chat',
        'date_time': '2013-10-27 15:29:19',
        'from_account': 'European Competitor <european.bbq.competitor>',
        'text': 'He is our new employee',
        'title': 'European Competitor, Echo123',
        'to_account': 'gen.beringer, echo123'}

    self.CheckEventValues(storage_writer, events[14], expected_event_values)

    # Test call event.
    expected_event_values = {
        'data_type': 'skype:event:call',
        'date_time': '2013-07-01 22:12:17',
        'dst_call': 'european.bbq.competitor',
        'src_call': 'gen.beringer',
        'user_start_call': False,
        'video_conference': False}

    self.CheckEventValues(storage_writer, events[22], expected_event_values)


if __name__ == '__main__':
  unittest.main()
