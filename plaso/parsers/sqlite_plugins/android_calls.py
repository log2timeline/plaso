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
"""This file contains a parser for the Android contacts2 Call History.

Android Call History is stored in SQLite database files named contacts2.db.
"""

from plaso.events import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidCallEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android Call History event."""

  DATA_TYPE = 'android:event:call'

  def __init__(
      self, java_time, usage, identifier, number, name, duration, call_type):
    """Initializes the event object.

    Args:
      java_time: The Java time value.
      usage: The description of the usage of the time value.
      identifier: The row identifier.
      number: The phone number associated to the remote party.
      duration: The number of seconds the call lasted.
      call_type: Incoming, Outgoing, or Missed.
    """
    super(AndroidCallEvent, self).__init__(java_time, usage)
    self.offset = identifier
    self.number = number
    self.name = name
    self.duration = duration
    self.call_type = call_type


class AndroidCallPlugin(interface.SQLitePlugin):
  """Parse Android contacts2 database."""

  NAME = 'android_calls'
  DESCRIPTION = u'Parser for Android calls SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ('SELECT _id AS id, date, number, name, duration, type FROM calls',
       'ParseCallsRow')]

  CALL_TYPE = {
      1: u'INCOMING',
      2: u'OUTGOING',
      3: u'MISSED'}

  def ParseCallsRow(
      self, parser_context, row, file_entry=None, parser_chain=None, query=None,
      **unused_kwargs):
    """Parses a Call record row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      query: Optional query string. The default is None.
    """
    # Extract and lookup the call type.
    call_type = self.CALL_TYPE.get(row['type'], u'UNKNOWN')

    event_object = AndroidCallEvent(
        row['date'], u'Call Started', row['id'], row['number'], row['name'],
        row['duration'], call_type)
    parser_context.ProduceEvent(
        event_object, parser_chain=parser_chain, file_entry=file_entry,
        query=query)

    duration = row['duration']
    if isinstance(duration, basestring):
      try:
        duration = int(duration, 10)
      except ValueError:
        duration = 0

    if duration:
      # The duration is in seconds and the date value in milli seconds.
      duration *= 1000
      event_object = AndroidCallEvent(
          row['date'] + duration, u'Call Ended', row['id'], row['number'],
          row['name'], row['duration'], call_type)
      parser_context.ProduceEvent(
          event_object, query=query, parser_chain=parser_chain,
          file_entry=file_entry)


sqlite.SQLiteParser.RegisterPlugin(AndroidCallPlugin)
