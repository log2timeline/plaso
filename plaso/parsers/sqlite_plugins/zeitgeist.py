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
"""Plugin for the Zeitgeist SQLite database.

   Zeitgeist is a service which logs the user activities and events, anywhere
   from files opened to websites visited and conversations.
"""
from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface


class ZeitgeistEvent(event.EventObject):
  """Convenience class for a Zeitgeist event."""
  DATA_TYPE = 'zeitgeist:activity'

  def __init__(self, timestamp, row_id, subject_uri):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      subject_uri: The Zeitgeist event.
    """
    super(ZeitgeistEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromJavaTime(timestamp)
    self.offset = row_id
    self.subject_uri = subject_uri


class ZeitgeistPlugin(interface.SQLitePlugin):
  """SQLite plugin for Zeitgeist activity database."""

  NAME = 'zeitgeist'

  # TODO: Explore the database more and make this parser cover new findings.

  QUERIES = [('SELECT id, timestamp, subj_uri FROM event_view',
             'ParseZeitgeistEventRow')]
  REQUIRED_TABLES = frozenset(['event', 'actor'])

  def ParseZeitgeistEventRow(self, unused_parser_context, row, **unused_kwargs):
    """Parses zeitgeist event row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.

    Yields:
      An event object (ZeitgeistEvent) containing the event
      data.
    """
    yield ZeitgeistEvent(row['timestamp'], row['id'], row['subj_uri'])
