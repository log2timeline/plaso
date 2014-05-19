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
"""Formatter for the Windows recycle files."""

from plaso.lib import errors
from plaso.lib import eventdata


class WinRecyclerFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Windows recycle bin events."""

  DATA_TYPE = 'windows:metadata:deleted_item'

  DRIVE_LIST = {
      0x00: 'A',
      0x01: 'B',
      0x02: 'C',
      0x03: 'D',
      0x04: 'E',
      0x05: 'F',
      0x06: 'G',
      0x07: 'H',
      0x08: 'I',
      0x09: 'J',
      0x0A: 'K',
      0x0B: 'L',
      0x0C: 'M',
      0x0D: 'N',
      0x0E: 'O',
      0x0F: 'P',
      0x10: 'Q',
      0x11: 'R',
      0x12: 'S',
      0x13: 'T',
      0x14: 'U',
      0x15: 'V',
      0x16: 'W',
      0x17: 'X',
      0x18: 'Y',
      0x19: 'Z',
  }

  # The format string.
  FORMAT_STRING_PIECES = [
      u'DC{index} ->',
      u'{orig_filename}',
      u'[{orig_filename_legacy}]',
      u'(from drive {drive_letter})']

  FORMAT_STRING_SHORT_PIECES = [
      u'Deleted file: {orig_filename}']

  SOURCE_LONG = 'Recycle Bin'
  SOURCE_SHORT = 'RECBIN'

  def GetMessages(self, event_object):
    """Return the message strings."""
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    if hasattr(event_object, 'drive_number'):
      event_object.drive_letter = self.DRIVE_LIST.get(
          event_object.drive_number, 'C?')

    return super(WinRecyclerFormatter, self).GetMessages(event_object)

