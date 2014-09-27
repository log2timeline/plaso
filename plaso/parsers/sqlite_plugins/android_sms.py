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
"""This file contains a parser for the Android SMS database.

Android SMS messages are stored in SQLite database files named mmssms.dbs.
"""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidSmsEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android SMS event."""

  DATA_TYPE = 'android:messaging:sms'

  def __init__(self, java_time, identifier, address, sms_read, sms_type, body):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      identifier: The row identifier.
      address: The phone number associated to the sender/receiver.
      status:  Read or Unread.
      type: Sent or Received.
      body: Content of the SMS text message.
    """
    super(AndroidSmsEvent, self).__init__(
        java_time, eventdata.EventTimestamp.CREATION_TIME)
    self.offset = identifier
    self.address = address
    self.sms_read = sms_read
    self.sms_type = sms_type
    self.body = body


class AndroidSmsPlugin(interface.SQLitePlugin):
  """Parse Android SMS database."""

  NAME = 'android_sms'

  # Define the needed queries.
  QUERIES = [
      ('SELECT _id AS id, address, date, read, type, body FROM sms',
       'ParseSmsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['sms'])

  SMS_TYPE = {
      1: u'RECEIVED',
      2: u'SENT'}
  SMS_READ = {
      0: u'UNREAD',
      1: u'READ'}

  def ParseSmsRow(self, parser_context, row, query=None, **unused_kwargs):
    """Parses an SMS row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Extract and lookup the SMS type and read status.
    sms_type = self.SMS_TYPE.get(row['type'], u'UNKNOWN')
    sms_read = self.SMS_READ.get(row['read'], u'UNKNOWN')

    event_object = AndroidSmsEvent(
        row['date'], row['id'], row['address'], sms_read, sms_type, row['body'])
    parser_context.ProduceEvent(
        event_object, plugin_name=self.NAME, query=query)


sqlite.SQLiteParser.RegisterPlugin(AndroidSmsPlugin)
