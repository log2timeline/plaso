#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
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
"""Parser for the Mac OS X launch services quarantine events."""
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class LsQuarantineEvent(event.EventObject):
  """Convenience class for a Mac OS X launch services quarantine event."""
  DATA_TYPE = 'macosx:lsquarantine'

  # TODO: describe more clearly what the data value contains.
  def __init__(self, timestamp, url, user_agent, data):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      url: The original URL of the file.
      user_agent: The user agent that was used to download the file.
      data: The data.
    """
    super(LsQuarantineEvent, self).__init__()

    self.timestamp = timelib.Timestamp.FromPosixTime(timestamp)
    self.timestamp_desc = eventdata.EventTimestamp.FILE_DOWNLOADED

    self.url = url
    self.agent = user_agent
    self.data = data


class LsQuarantineParser(parser.SQLiteParser):
  """Parses the launch services quarantine events database.

     The LS quarantine events are stored in SQLite database files named
     /Users/<username>/Library/Preferences/\
         QuarantineEvents.com.apple.LaunchServices
  """

  # Define the needed queries.
  # TODO: move the timestamp adjustment into code and make sure to change
  # the corresponding docstring of LsQuarantineEvent.
  QUERIES = [(('SELECT LSQuarantineTimestamp+978328800 AS Epoch, LSQuarantine'
               'AgentName AS Agent, LSQuarantineOriginURLString AS URL, '
               'LSQuarantineDataURLString AS Data FROM LSQuarantineEvent '
               'ORDER BY Epoch'), 'ParseLSQuarantineRow')]

  # The required tables.
  REQUIRED_TABLES = ('LSQuarantineEvent',)

  __pychecker__ = 'unusednames=kwargs'
  def ParseLSQuarantineRow(self, row, **kwargs):
    """Parses a launch services quarantine event row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (LsQuarantineEvent) containing the event data.
    """
    yield LsQuarantineEvent(
        row['Epoch'], row['URL'], row['Agent'], row['Data'])

