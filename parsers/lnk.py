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

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import parser


# TODO: description_long and description_short are there for legacy reasons.
class WinLnkEventData(object):
  """The Windows Shortcut (LNK) event data."""

  def __init__(self, lnk_file):
    """Initializes the event data.

    Keeps a local copy of the required data so the file object can be
    dereferenced.

    Args:
      lnk_file: the Windows Shortcut (LNK) file object (pylnk.file).
    """
    super(WinLnkEventData, self).__init__()

    self._description_long = u''
    self._description_short = u''

    self.description = lnk_file.get_description()
    self.local_path = lnk_file.get_local_path()
    self.network_path = lnk_file.get_network_path()
    self.command_line_arguments = lnk_file.get_command_line_arguments()
    self.env_variables_location = lnk_file.get_environment_variables_location()
    self.relative_path = lnk_file.get_relative_path()
    self.working_directory = lnk_file.get_working_directory()
    self.icon_location = lnk_file.get_icon_location()

  @property
  def linked_path(self):
    if not self.local_path:
      return self.network_path
    return self.local_path

  @property
  def description_long(self):
    class TextList(list):
      """List with support to add description, value pairs."""
      def AppendValue(self, description, value):
        """Appends a non-empty value and its description to the list."""
        if value:
           super(TextList, self).append(
               u'{0}: {1}'.format(description, value))

    if not self._description_long:
      text_list = TextList()

      text_list.append(u'[{0}] '.format(self.description))

      text_list.AppendValue('Local path', self.local_path)
      text_list.AppendValue('Network path', self.network_path)
      text_list.AppendValue('cmd arguments', self.command_line_arguments)
      text_list.AppendValue('env location', self.env_variables_location)
      text_list.AppendValue('Relative path', self.relative_path)
      text_list.AppendValue('Working dir', self.working_directory)
      text_list.AppendValue('Icon location', self.icon_location)

      self._description_long = u' '.join(text_list)

    return self._description_long

  @property
  def description_short(self):
    if not self._description_short:
      self._description_short = u'[{0}] {1} {2}'.format(
          getattr(self, 'description', u'Empty Description'),
          self.linked_path,
          getattr(self, 'command_line_arguments', u''))

      if len(self._description_short) > 80:
        self._description_short = self._description_short[:79]
    return self._description_short


class WinLnkParser(parser.PlasoParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = 'WinLnkParser'
  PARSER_TYPE = 'LNK'

  def Parse(self, file_object):
    """Extract data from a Windows Shortcut (LNK) file.

    Args:
      file_object: a file-like object to read data from.

    Returns:
      an event container (WinLnkEventContainer) that contains the parsed
      attributes.
    """
    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(getattr(self._pre_obj, 'codepage', 'cp1252'))

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.NAME, file_object.name, exception))

    event_container = event.EventContainer()

    event_container.offset = 0
    event_container.source_long = self.NAME
    event_container.source_short = self.PARSER_TYPE

    event_data = WinLnkEventData(lnk_file)

    # TODO: description_long and description_short are there for legacy reasons.
    event_container.description_long = event_data.description_long
    event_container.description_short = event_data.description_short

    # TODO: change description_long in each sub event when container design
    # has been simplified.
    event_container.Append(event.FiletimeEvent(
        lnk_file.get_file_access_time_as_integer(),
        'Last Access Time', event_data.description_long))

    event_container.Append(event.FiletimeEvent(
        lnk_file.get_file_creation_time_as_integer(),
        'Creation Time', event_data.description_long))

    event_container.Append(event.FiletimeEvent(
        lnk_file.get_file_modification_time_as_integer(),
        'Modification Time', event_data.description_long))

    # TODO: add support for the distributed link tracker
    # TODO: add support for the shell item

    return event_container
