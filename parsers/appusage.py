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
"""This file contains a parser for the Mac OS X application usage.

   The application usage is stored in SQLite database files named
   /var/db/application_usage.sqlite
"""
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib


class MacOSXApplicationUsageEvent(event.EventObject):
  """Convenience class for a Mac OS X application usage event."""
  DATA_TYPE = 'macosx:application_usage'

  def __init__(self, timestamp, usage, application_name, application_version,
               bundle_id, number_of_times):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      usage: The description of the usage of the time value.
      application_name: The name of the application.
      application_version: The version of the application.
      bundle_id: The bundle identifier of the application.
      number_of_times: TODO: number of times what?
    """
    super(MacOSXApplicationUsageEvent, self).__init__()

    self.timestamp = timestamp
    # TODO: replace usage by definition(s) in eventdata. Not sure which values
    # it will hold here.
    self.timestamp_desc = usage

    self.source_short = 'LOG'
    self.source_long = 'Application Usage'

    self.application = application_name
    self.app_version = application_version
    self.bundle_id = bundle_id
    self.count = number_of_times


class ApplicationUsageParser(parser.SQLiteParser):
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
              'ParseApplicationUsageRow')]

  # The required tables.
  REQUIRED_TABLES = ('application_usage',)

  __pychecker__ = 'unusednames=kwargs'
  def ParseApplicationUsageRow(self, row, **kwargs):
    """Parses an application usage row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (MacOSXApplicationUsageEvent) containing the event
      data.
     """
    yield MacOSXApplicationUsageEvent(
        timelib.TimeStamp.FromPosixTime(row['last_time']),
        u'Application %s' % row['event'], u'%s' % row['app_path'],
        row['app_version'], row['bundle_id'], row['number_times'])


class ApplicationUsageFormatter(eventdata.EventFormatter):
  """Define the formatting for Application Usage information."""
  DATA_TYPE = 'macosx:application_usage'

  FORMAT_STRING = (u'{application} v.{app_version} (bundle: {bundle_id}).'
                   ' Launched: {count} time(s)')
  FORMAT_STRING_SHORT = u'{application} ({count} time(s))'

