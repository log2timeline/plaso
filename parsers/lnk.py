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
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser

import pylnk


if pylnk.get_version() < '20130304':
  raise ImportWarning('WinLnkParser requires at least pylnk 20130304.')


class WinLnkLinkEventContainer(event.EventContainer):
  """Convenience class for a Windows Shortcut (LNK) link event container."""

  def __init__(self, lnk_file):
    """Initializes the event container.

    Args:
      lnk_file: The LNK file (pylnk.file).
    """
    super(WinLnkLinkEventContainer, self).__init__()

    self.data_type = 'windows:lnk:link'

    # TODO: refactor to formatter.
    self.source_long = 'WinLnkParser'
    self.source_short = 'LNK'

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

    container = WinLnkLinkEventContainer(lnk_file)

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_access_time_as_integer(),
        eventdata.EventTimestamp.ACCESS_TIME,
        container.data_type))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_creation_time_as_integer(),
        eventdata.EventTimestamp.CREATION_TIME,
        container.data_type))

    container.Append(event.FiletimeEvent(
        lnk_file.get_file_modification_time_as_integer(),
        eventdata.EventTimestamp.MODIFICATION_TIME,
        container.data_type))

    # TODO: add support for the distributed link tracker.
    # TODO: add support for the shell item.

    return container

