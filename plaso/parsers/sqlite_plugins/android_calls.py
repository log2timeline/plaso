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
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEvent(event.EventObject):
  """Convenience class for an Android Call History event."""

  DATA_TYPE = 'android:event:call'
  def __init__(self, timestamp, number, name, duration, call_type,
          timestamp_desc):
    """Initializes the event object.
    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of milliseconds since Jan 1, 1970 00:00:00 UTC.
      timestamp_desc: Call Started, Call Ended.
      number: The phone number associated to the remote party.
      duration: The number of seconds the call lasted.
      call_type: Incoming, Outgoing, or Missed.
    """
    super(AndroidCallEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromJavaTime(timestamp)
    self.timestamp_desc = timestamp_desc
    self.number = number
    self.name = name
    self.duration = duration
    self.call_type = call_type


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = 'android_calls'

  # Define the needed queries.
  QUERIES = [((u'SELECT _id AS id, date, number, name, duration, type '
               u'FROM calls'), 'ParseCallsRow')]

  CALL_TYPE = {
      1: 'INCOMING',
      2: 'OUTGOING',
      3: 'MISSED'
    }

  def ParseCallsRow(self, row):
    """Parses a Call record row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (AndroidCallEvent) containing the event data.
    """

    # Extract and lookup the call type.
    call_type = self.CALL_TYPE.get(row['type'], 'UNKNOWN')

    yield AndroidCallEvent(
        row['date'], row['number'], row['name'], row['duration'], call_type,
        'Call Started')

    try:
      duration = int(row['duration'])
      if duration:
        yield AndroidCallEvent(
            row['date'] + duration * 1000, row['number'], row['name'],
            row['duration'], call_type, 'Call Ended')
    except ValueError:
      pass
