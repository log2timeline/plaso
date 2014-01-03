#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains few methods for Plaso."""

import binascii
import os

from plaso.pvfs import pfile


def GetEventData(event_object, before=0, length=20):
  """Returns a hexadecimal representation of the event data.

     This function creates a hexadecimal string representation based on
     the event data described by the event object.

  Args:
    event_object: The event object (instance of EventObject).
    before: Optional number of bytes to include in the output before the event.
            The default is none.
    length: Optional number of lines to include in the output.
            The default is 20.

  Returns:
    A string that contains the hexadecimal representation of the event data.
  """
  if not event_object:
    return u'Missing event object.'

  if not hasattr(event_object, 'pathspec'):
    return u'Event object has no path specification.'

  try:
    path_spec = event_object.pathspec.ToProto()
    file_entry = pfile.PFileResolver.OpenFileEntry(path_spec)
  except IOError as e:
    return u'Unable to open file with error: {0:s}'.format(e)

  offset = getattr(event_object, 'offset', 0)
  if offset - before > 0:
    offset -= before

  file_object = file_entry.Open()
  file_object.seek(offset, os.SEEK_SET)
  data = file_object.read(int(length) * 16)
  file_object.close()

  return GetHexDump(data, offset)


def GetHexDump(data, offset=0):
  """Returns a hexadecimal representation of the contents of a binary string.

     All ASCII characters in the hexadecimal representation (hexdump) are
     translated back to their character representation.

  Args:
    data: The binary string.
    offset: An optional start point in bytes where the data lies, for
            presentation purposes.

  Returns:
    A string that contains the hexadecimal representation of the binary string.
  """
  hexdata = binascii.hexlify(data)
  data_out = []

  for entry_nr in range(0, len(hexdata) / 32):
    point = 32 * entry_nr
    data_out.append(GetHexDumpLine(hexdata[point:point + 32], offset, entry_nr))

  if len(hexdata) % 32:
    breakpoint = len(hexdata) / 32
    leftovers = hexdata[breakpoint:]
    pad = ' ' * (32 - len(leftovers))

    data_out.append(GetHexDumpLine(leftovers + pad, offset, breakpoint))

  return '\n'.join(data_out)


def GetHexDumpLine(line, orig_ofs, entry_nr=0):
  """Returns a single line of 'xxd'-like hexadecimal representation."""
  out = []
  out.append('{0:07x}: '.format(orig_ofs + entry_nr * 16))

  for bit in range(0, 8):
    out.append('%s ' % line[bit * 4:bit * 4 + 4])

  for bit in range(0, 16):
    try:
      data = binascii.unhexlify(line[bit * 2: bit * 2 + 2])
    except TypeError:
      data = '.'

    if ord(data) > 31 and ord(data) < 128:
      out.append(data)
    else:
      out.append('.')
  return ''.join(out)
