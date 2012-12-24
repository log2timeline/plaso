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
"""This file contains a parser for Windows Shortcut (LNK) files."""
import logging
import pylnk

from plaso.lib import event
from plaso.lib import parser
from plaso.lib import timelib

# TODO: description_long and description_short are there for legacy
# reasons, they currently mess up the flow of the code. Remove them
# if we have a good alternative.

# TODO: this class can likely be replaced by a more generic container
# e.g. the text list could be moved into the class. Leaving as-is
# but refactor it to lib/event.py after implementing the EVT/EVTX
# parsers.
class LnkEventContainer(event.EventContainer):
  """Container for Windows Shortcut (LNK) event data."""

  def __init__(self, source_long, source_short, description_short):
    """Initializes the LNK event container.

    Args:
      source_long: A string containing the long source.
      source_short: A string containing the short source.
      description_short: A string containing the short description (LEGACY).
    """
    super(LnkEventContainer, self).__init__()

    self.offset = 0
    self.source_long = source_long
    self.source_short = source_short

    if len(description_short) > 80:
      self.description_short = description_short[:79]
    else:
      self.description_short = description_short

  def AddFiletimeEvent(self, description, timestamp, description_long):
    """Adds a FILETIME timestamp as an event object.

    Args:
      description: the description of the usage of the timestamp.
      timestamp: the FILETIME timestamp value.
      description_long: the long description (LEGACY).
    """
    event_object = event.EventObject()
    event_object.timestamp_desc = description
    event_object.timestamp = timelib.WinFiletime2Unix(timestamp)
    event_object.description_long = description_long

    self.Append(event_object)


class WinLnk(parser.PlasoParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = 'Shortcut File'
  PARSER_TYPE = 'LNK'

  def Parse(self, file_object):
    """Extract link data from a Windows Shortcut file.

    Args:
      file_object: a file-like object to read data from.

    Returns:
      an instance of EventContainer, which contains the parsed attributes.
    """
    class TextList(list):
      """List with support to add description, value pairs."""
      def AppendValue(self, description, value):
        """Appends a non-empty value and its description to the list."""
        if value:
           super(TextList, self).append(
               u'{0}: {1}'.format(description, value))

    lnk_file = pylnk.file()
    lnk_file.open_file_object(file_object)

    text_list = TextList()

    text_list.append(u'[{0}] '.format(lnk_file.description))

    text_list.AppendValue('Local path', lnk_file.local_path)
    text_list.AppendValue('Network path', lnk_file.network_path)
    text_list.AppendValue(
        'cmd arguments', lnk_file.command_line_arguments)
    text_list.AppendValue(
        'env location', lnk_file.get_environment_variables_location())
    text_list.AppendValue('Relative path', lnk_file.relative_path)
    text_list.AppendValue('Working dir', lnk_file.working_directory)
    text_list.AppendValue('Icon location', lnk_file.get_icon_location())

    # TODO: description_long and description_short are there for legacy
    # reasons, they currently mess up the flow of the code. Remove them
    # if we have a good alternative.
    if lnk_file.description:
      description = lnk_file.description
    else:
      description = u'Empty Description'

    if lnk_file.command_line_arguments:
      cli = lnk_file.command_line_arguments
    else:
      cli = u''

    linked_path = lnk_file.local_path
    if not linked_path:
      linked_path = lnk_file.network_path

    description_long = u' '.join(text_list)
    description_short = u'[{0}] {1} {2}'.format(
      description, linked_path, cli)

    event_container = LnkEventContainer(
        self.NAME, self.PARSER_TYPE, description_short)

    if not description_long:
      logging.warning(
          u'Unable to extract information from: %s', file_object.name)
    else:
      timestamp = lnk_file.get_file_access_time_as_integer()
      event_container.AddFiletimeEvent(
          'Last Access Time', timestamp, description_long)

      timestamp = lnk_file.get_file_creation_time_as_integer()
      event_container.AddFiletimeEvent(
          'Creation Time', timestamp, description_long)

      timestamp = lnk_file.get_file_modification_time_as_integer()
      event_container.AddFiletimeEvent(
          'Modification Time', timestamp, description_long)

      # TODO: add support for the shell item?

    return event_container

