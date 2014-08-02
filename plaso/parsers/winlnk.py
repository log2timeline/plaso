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

  def __init__(self, timestamp, timestamp_description, lnk_file):
    """Initializes the event.

    Args:
      timestamp: The FILETIME value for the timestamp.
      timestamp_description: The usage string for the timestamp value.
      lnk_file: The LNK file (pylnk.file).
    """
    super(WinLnkLinkEvent, self).__init__(timestamp, timestamp_description)

    self.data_type = 'windows:lnk:link'

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


class WinLnkParser(interface.BaseParser):
  """Parses Windows Shortcut (LNK) files."""

  NAME = 'lnk'

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(WinLnkParser, self).__init__(pre_obj, config)
    self._codepage = getattr(self._pre_obj, 'codepage', 'cp1252')

  def Parse(self, file_entry):
    """Extract data from a Windows Shortcut (LNK) file.

    Args:
      file_entry: A file entry object.

    Yields:
      An event object (instance of WinLnkLinkEvent) that contains the parsed
      attributes.
    """
    file_object = file_entry.GetFileObject()
    lnk_file = pylnk.file()
    lnk_file.set_ascii_codepage(self._codepage)

    try:
      lnk_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file {1:s}: {2:s}'.format(
          self.parser_name, file_entry.name, exception))

    yield WinLnkLinkEvent(
        lnk_file.get_file_access_time_as_integer(),
        eventdata.EventTimestamp.ACCESS_TIME, lnk_file)

    yield WinLnkLinkEvent(
        lnk_file.get_file_creation_time_as_integer(),
        eventdata.EventTimestamp.CREATION_TIME, lnk_file)

    yield WinLnkLinkEvent(
        lnk_file.get_file_modification_time_as_integer(),
        eventdata.EventTimestamp.MODIFICATION_TIME, lnk_file)

    if lnk_file.link_target_identifier_data:
      shell_items_parser = shell_items.ShellItemsParser(file_entry.name)
      for event_object in shell_items_parser.Parse(
          lnk_file.link_target_identifier_data, codepage=self._codepage):
        yield event_object

    # TODO: add support for the distributed link tracker.

    file_object.close()
