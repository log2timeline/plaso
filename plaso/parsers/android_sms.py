#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# Shut up pylint
# * R0201: Method could be a function
# pylint: disable=R0201

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class AndroidSmsEvent(event.EventObject):
  """Convenience class for an Android SMS event."""
  DATA_TYPE = 'android:messaging:sms'
  def __init__(self, timestamp, address, sms_read, sms_type, body):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of milliseconds since Jan 1, 1970 00:00:00 UTC.
      address: The phone number associated to the sender/receiver.
      status:  Read or Unread.
      type: Sent or Received.
      body: Content of the SMS text message.
    """
    super(AndroidSmsEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromJavaTime(timestamp)
    self.timestamp_desc = eventdata.EventTimestamp.CREATION_TIME
    self.address = address
    self.sms_read = sms_read
    self.sms_type = sms_type
    self.body = body


class AndroidSmsParser(parser.SQLiteParser):
  """Parse Android SMS database."""
  # Define the needed queries.
  QUERIES = [((u'SELECT _id AS id, address, date, read, type, '
               u'body FROM sms'), 'ParseSmsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['sms'])

  SMS_TYPE = {
      1: 'RECEIVED',
      2: 'SENT'
    }
  SMS_READ = {
      0: 'UNREAD',
      1: 'READ'
    }

  def ParseSmsRow(self, row, **dummy_kwargs):
    """Parses an SMS row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (AndroidSmsEvent) containing the event data.
    """

    # Extract and lookup the SMS type and read status.
    sms_type = self.SMS_TYPE.get(row['type'], 'UNKNOWN')
    sms_read = self.SMS_READ.get(row['read'], 'UNKNOWN')

    yield AndroidSmsEvent(
        row['date'], row['address'], sms_read, sms_type, row['body'])
