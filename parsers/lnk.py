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
"""Parser for Windows Shortcut (LNK) files."""
import pylnk
import re

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


if pylnk.get_version() < "20130117":
  raise ImportWarning("WinLnkParser requires at least pylnk 20130117.")


class WinLnkParser(parser.PlasoParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = 'WinLnkParser'
  PARSER_TYPE = 'LNK'

  def Parse(self, file_object):
    """Extract data from a Windows Shortcut (LNK) file.

    Args:
      file_object: a file-like object to read data from.

    Returns:
      an event container (EventContainer) that contains the parsed
      attributes.
    """
    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(getattr(self._pre_obj, 'codepage', 'cp1252'))

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.NAME, file_object.name, exception))

    container = event.EventContainer()

    container.offset = 0
    container.source_long = self.NAME
    container.source_short = self.PARSER_TYPE

    container.description = lnk_file.description
    container.local_path = lnk_file.local_path
    container.network_path = lnk_file.network_path
    container.command_line_arguments = lnk_file.command_line_arguments
    container.env_var_location = lnk_file.environment_variables_location
    container.relative_path = lnk_file.relative_path
    container.working_directory = lnk_file.working_directory
    container.icon_location = lnk_file.icon_location

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_access_time_as_integer(),
        eventdata.EventTimestamp.ACCESS_TIME))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_creation_time_as_integer(),
        eventdata.EventTimestamp.CREATION_TIME))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_modification_time_as_integer(),
        eventdata.EventTimestamp.MODIFICATION_TIME))

    # TODO: add support for the distributed link tracker.
    # TODO: add support for the shell item.

    return container


class WinLnkFormatter(eventdata.ConditionalEventFormatter):
  """Class that formats Windows Shortcut (LNK) events."""
  ID_RE = re.compile('WinLnkParser:', re.DOTALL)

  # The format string.
  FORMAT_STRING_PIECES = [
      u'[{description}]',
      u'Local path: {local_path}',
      u'Network path: {network_path}',
      u'cmd arguments: {command_line_arguments}',
      u'env location: {env_var_location}',
      u'Relative path: {relative_path}',
      u'Working dir: {working_directory}',
      u'Icon location: {icon_location}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{description}]',
      u'{linked_path}',
      u'{command_line_arguments}']

  def _GetLinkedPath(self, event_object):
    """Determines the linked path.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A string containing the linked path.
    """
    if hasattr(event_object, 'local_path'):
      return event_object.local_path

    if hasattr(event_object, 'network_path'):
      return event_object.network_path

    if hasattr(event_object, 'relative_path'):
      paths = []
      if hasattr(event_object, 'working_directory'):
        paths.append(event_object.working_directory)
      paths.append(event_object.relative_path)

      return u'\\'.join(paths)

    return 'Unknown'

  def GetMessages(self, event_object):
    """Returns a list of messages extracted from an event object.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A list that contains both the longer and shorter version of the message
      string.
    """
    # Update event object with a description if necessary.
    if not hasattr(event_object, 'description'):
      event_object.description = u'Empty description'

    # Update event object with the linked path.
    event_object.linked_path = self._GetLinkedPath(event_object)

    return super(WinLnkFormatter, self).GetMessages(event_object)
