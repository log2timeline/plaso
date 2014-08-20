#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""Parser for Windows Shortcut (LNK) files."""

import pylnk

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers.shared import shell_items


if pylnk.get_version() < '20130304':
  raise ImportWarning('WinLnkParser requires at least pylnk 20130304.')


class WinLnkLinkEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Shortcut (LNK) link event."""
 
  DATA_TYPE = 'windows:lnk:link'

  def __init__(self, timestamp, timestamp_description, lnk_file, link_target):
    """Initializes the event object.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      lnk_file: The LNK file (instance of pylnk.file).
      link_target: String representation of the link target shell item list
                   or None.
    """
    super(WinLnkLinkEvent, self).__init__(timestamp, timestamp_description)

    self.offset = 0
    self.file_size = lnk_file.file_size
    self.file_attribute_flags = lnk_file.file_attribute_flags
    self.drive_type = lnk_file.drive_type
    self.drive_serial_number = lnk_file.drive_serial_number
    self.description = lnk_file.description
    self.volume_label = lnk_file.volume_label
    self.local_path = lnk_file.local_path
    self.network_path = lnk_file.network_path
    self.command_line_arguments = lnk_file.command_line_arguments
    self.env_var_location = lnk_file.environment_variables_location
    self.relative_path = lnk_file.relative_path
    self.working_directory = lnk_file.working_directory
    self.icon_location = lnk_file.icon_location

    if link_target:
      self.link_target = link_target


class WinLnkParser(interface.BaseParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = 'lnk'

  def Parse(self, parser_context, file_entry):
    """Extract data from a Windows Shortcut (LNK) file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    file_object = file_entry.GetFileObject()
    self.ParseFileObject(parser_context, file_object, file_entry=file_entry)
    file_object.close()

  def ParseFileObject(
      self, parser_context, file_object, file_entry=None, display_name=None):
    """Parses a Windows Shortcut (LNK) file.

    The file entry is used to determine the display name if it was not provided.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_object: A file-like object.
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      display_name: Optional display name.
    """
    if not display_name and file_entry:
      display_name = parser_context.GetDisplayName(file_entry)

    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(parser_context.codepage)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s} with error: {2:s}'.format(
              self.NAME, display_name, exception))

    link_target = None
    if lnk_file.link_target_identifier_data:
      # TODO: change file_entry.name to display name once it is generated
      # correctly.
      if file_entry:
        display_name = file_entry.name

      shell_items_parser = shell_items.ShellItemsParser(display_name)
      shell_items_parser.Parse(
          parser_context, lnk_file.link_target_identifier_data,
          codepage=parser_context.codepage)

      link_target = shell_items_parser.CopyToPath()

    parser_context.ProduceEvents(
        [WinLnkLinkEvent(
            lnk_file.get_file_access_time_as_integer(),
            eventdata.EventTimestamp.ACCESS_TIME, lnk_file, link_target),
        WinLnkLinkEvent(
            lnk_file.get_file_creation_time_as_integer(),
            eventdata.EventTimestamp.CREATION_TIME, lnk_file, link_target),
        WinLnkLinkEvent(
            lnk_file.get_file_modification_time_as_integer(),
            eventdata.EventTimestamp.MODIFICATION_TIME, lnk_file, link_target)],
        parser_name=self.NAME, file_entry=file_entry)

    # TODO: add support for the distributed link tracker.
