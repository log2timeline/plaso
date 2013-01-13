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


class ApplicationUsage(parser.SQLiteParser):
  """Parse Application Usage history files.

  Application usage is a SQLite database that logs down entries
  triggered by NSWorkspaceWillLaunchApplicationNotification and
  NSWorkspaceDidTerminateApplicationNotification NSWorkspace notifications by
  crankd.

  See the code here:
  http://code.google.com/p/google-macops/source/browse/trunk/crankd/\
      ApplicationUsage.py

  Default installation: /var/db/application_usage.sqlite
  """

  NAME = 'Application Usage'

  # Define the needed queries.
  QUERIES = [(('SELECT last_time, event, bundle_id, app_version, app_path,'
               'number_times FROM application_usage ORDER BY last_time'),
              'ParseApplicationUsage')]

  # The required tables.
  REQUIRED_TABLES = ('application_usage',)

  DATE_MULTIPLIER = 1000000

  def ParseApplicationUsage(self, row, **_):
    """Return an EventObject from an application usage record."""
    source = u'Application %s' % row['event']

    date = row['last_time'] * self.DATE_MULTIPLIER

    evt = event.SQLiteEvent(date, source, 'LOG', self.NAME)
    evt.application = u'%s' % row['app_path']
    evt.app_version = row['app_version']
    evt.bundle_id = row['bundle_id']
    evt.count = row['number_times']

    yield evt


class ApplicationUsageFormatter(eventdata.EventFormatter):
  """Define the formatting for Application Usage information."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('ApplicationUsage:Application Usage', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'{application} v.{app_version} (bundle: {bundle_id}).'
                   ' Launched: {count} time(s)')
  FORMAT_STRING_SHORT = u'{application} ({count} time(s))'

