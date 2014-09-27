#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""This file contains a parser for the Android usage-history.xml file."""

import os

from xml.etree import ElementTree
from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


class AndroidAppUsageEvent(event.EventObject):
  """EventObject for an Android Application Last Resumed event."""

  DATA_TYPE = 'android:event:last_resume_time'

  def __init__(self, last_resume_time, package, component):
    """Initializes the event object.

    Args:
      last_resume_time: The Last Resume Time of an Android App with details of
           individual components. The timestamp contains the number of
           milliseconds since Jan 1, 1970 00:00:00 UTC.
      package: The name of the Android App.
      component: The individual component of the App.
    """
    super(AndroidAppUsageEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromJavaTime(last_resume_time)
    self.package = package
    self.component = component

    self.timestamp_desc = eventdata.EventTimestamp.LAST_RESUME_TIME


class AndroidAppUsageParser(interface.BaseParser):
  """Parses the Android usage-history.xml file."""

  NAME = 'android_app_usage'
  DESCRIPTION = u'Parser for the Android usage-history.xml file.'

  def Parse(self, parser_context, file_entry):
    """Extract the Android usage-history file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    file_object = file_entry.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    # Need to verify the first line to make sure this is a) XML and
    # b) the right XML.
    first_line = text_file_object.readline(90)

    # Note that we must check the data here as a string first, otherwise
    # forcing first_line to convert to Unicode can raise a UnicodeDecodeError.
    if not first_line.startswith('<?xml'):
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [not XML]')

    # We read in the second line due to the fact that ElementTree
    # reads the entire file in memory to parse the XML string and
    # we only care about the XML file with the correct root key,
    # which denotes a typed_history.xml file.
    second_line = text_file_object.readline(50).strip()

    if second_line != u'<usage-history>':
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [wrong XML root key]')

    # For ElementTree to work we need to work on a filehandle seeked
    # to the beginning.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)
    root = xml.getroot()

    for app in root:
      for part in app.iter():
        if part.tag == 'comp':
          package = app.get(u'name', '')
          component = part.get(u'name', '')

          try:
            last_resume_time = int(part.get('lrt', u''), 10)
          except ValueError:
            continue

          event_object = AndroidAppUsageEvent(
              last_resume_time, package, component)
          parser_context.ProduceEvent(
              event_object, parser_name=self.NAME, file_entry=file_entry)

    file_object.close()


manager.ParsersManager.RegisterParser(AndroidAppUsageParser)
