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

    container.description = lnk_file.get_description()
    container.local_path = lnk_file.get_local_path()
    container.network_path = lnk_file.get_network_path()
    container.command_line_arguments = lnk_file.get_command_line_arguments()
    container.env_var_location = lnk_file.get_environment_variables_location()
    container.relative_path = lnk_file.get_relative_path()
    container.working_directory = lnk_file.get_working_directory()
    container.icon_location = lnk_file.get_icon_location()

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_access_time_as_integer(),
        'Last Access Time'))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_creation_time_as_integer(),
        'Creation Time'))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_modification_time_as_integer(),
        'Modification Time'))

    # TODO: add support for the distributed link tracker
    # TODO: add support for the shell item

    return container


class WinLnkFormatter(eventdata.EventFormatter):
  """Define the formatting for Windows shortcut."""
  #TODO: Change this into a more generic formatter that can be easily extended
  # for similar parsers.

  ID_RE = re.compile('WinLnkParser:', re.DOTALL)

  # The format string.
  FORMAT_STRING = u''
  FORMAT_STRING_SHORT = u''

  # The format string.
  # TODO: use as part of the conditional formatter.
  FORMAT_STRING_PIECES = [
      u'[{description}]',
      u'Local path: {local_path}',
      u'Network path: {network_path}',
      u'cmd arguments: {command_line_arguments}',
      u'env location: {env_variables_location}',
      u'Relative path: {relative_path}',
      u'Working dir: {working_directory}',
      u'Icon location: {icon_location}']

  def GetLinkedPath(self, event_object):
    """Determines the linked path.

    Args:
      event_object: The event object (EventObject) containing the event
                    specific data.

    Returns:
      A string containing the linked path.
    """
    if hasattr(event_object, 'local_path'):
      return event_object['local_path']

    if hasattr(event_object, 'network_path'):
      return event_object['network_path']

    if hasattr(event_object, 'relative_path'):
      paths = []
      if hasattr(event_object, 'working_directory'):
        paths.append(event_object['working_directory'])
      paths.append(event_object['relative_path'])

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
    class TextList(list):
      """List with support to add description, value pairs."""

      def __init__(self, attributes):
        """Store the attributes for future lookups."""
        super(TextList, self).__init__()
        self._attributes = attributes

      def AppendValue(self, description, value):
        """Appends a non-empty value and its description to the list."""
        __pychecker__ = 'missingattrs=_attributes'
        if value in self._attributes:
          if description:
            super(TextList, self).append(
                u'{0}: {{{1}}}'.format(description, value))
          else:
            super(TextList, self).append(u'{{{0}}}'.format(value))

    # Update extended attributes with the linked path.
    if not hasattr(event_object, 'description'):
      event_object.description = u'Empty description'

    # Check if we have "fixed" the format strings.
    if not self.format_string:
      format_short = TextList(event_object.attributes)
      format_long = TextList(event_object.attributes)

      format_long.append(u'[{description}]')
      format_short.append(u'[{description}]')

      format_long.AppendValue('Local path', 'local_path')
      format_long.AppendValue('Network path', 'network_path')
      format_long.AppendValue('cmd arguments', 'command_line_arguments')
      format_long.AppendValue('env location', 'env_var_location')
      format_long.AppendValue('Relative path', 'relative_path')
      format_long.AppendValue('Working dir', 'working_directory')
      format_long.AppendValue('Icon location', 'icon_location')

      format_short.AppendValue('', self.GetLinkedPath(event_object))
      format_short.AppendValue('', 'command_line_arguments')

      self.format_string = u' '.join(format_long)
      self.format_string_short = u' '.join(format_short)

    return super(WinLnkFormatter, self).GetMessages(event_object)

