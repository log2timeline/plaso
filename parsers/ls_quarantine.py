#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains a parser for application usage in plaso."""
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class LsQuarantine(parser.SQLiteParser):
  """Parse the LaunchServices.QuarantineEvents databse on Mac OS X.

  File can be found here:
    /Users/<username>/Library/Preferences/com.apple.LaunchServices.\
        QuarantineEvents
  """

  NAME = 'LS Quarantine'

  # Define the needed queries.
  QUERIES = [(('SELECT LSQuarantineTimestamp+978328800 AS Epoch, LSQuarantine'
               'AgentName AS Agent, LSQuarantineOriginURLString AS URL, LSQua'
               'rantineDataURLString AS Data FROM LSQuarantineEvent ORDER BY '
               'Epoch'), 'ParseLSQuarantine')]

  # The required tables.
  REQUIRED_TABLES = ('LSQuarantineEvent',)

  DATE_MULTIPLIER = 1000000

  def ParseLSQuarantine(self, row, **_):
    """Return an EventObject from Parse LS QuarantineEvent record."""
    date = int(row['Epoch'] * self.DATE_MULTIPLIER)

    evt = event.SQLiteEvent(date, 'File Downloaded', 'HIST',
                            u'%s Download Event' % self.NAME)

    evt.agent = row['Agent']
    evt.url = row['URL']
    evt.data = row['Data']

    yield evt


class LSQuarantineFormatter(eventdata.PlasoFormatter):
  """Define the formatting for LS Quarantine history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('LS Qurantine:', re.DOTALL)

  # The format string.
  FORMAT_STRING = u'[{agent}] Downloaded: {url} <{data}>'
  FORMAT_STRING_SHORT = u'{url}'

