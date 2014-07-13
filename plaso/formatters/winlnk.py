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
"""Formatter for Windows Shortcut (LNK) files."""

from plaso.lib import errors
from plaso.formatters import interface


class WinLnkLinkFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Shortcut (LNK) link event."""

  DATA_TYPE = 'windows:lnk:link'

  FORMAT_STRING_PIECES = [
      u'[{description}]',
      u'File size: {file_size}',
      u'File attribute flags: 0x{file_attribute_flags:08x}',
      u'Drive type: {drive_type}',
      u'Drive serial number: 0x{drive_serial_number:08x}',
      u'Volume label: {volume_label}',
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

  SOURCE_LONG = 'Windows Shortcut'
  SOURCE_SHORT = 'LNK'

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
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    # Update event object with a description if necessary.
    if not hasattr(event_object, 'description'):
      event_object.description = u'Empty description'

    # Update event object with the linked path.
    event_object.linked_path = self._GetLinkedPath(event_object)

    return super(WinLnkLinkFormatter, self).GetMessages(event_object)
