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
"""Frontend utility classes and functions."""

import binascii
import tempfile
import os

from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import timelib


# TODO: add tests for the functions in this class.
class OutputWriter(object):
  """Class that defines output writing methods for the frontends and tools."""

  DATA_BUFFER_SIZE = 32768

  @classmethod
  def GetDateTimeString(cls, timestamp):
    """Returns a human readable date and time string in the ISO 8601 format."""
    return timelib.Timestamp.CopyToIsoFormat(timestamp)

  @classmethod
  def GetEventDataHexDump(cls, event_object, before=0, length=20):
    """Returns a hexadecimal representation of the event data.

       This function creates a hexadecimal string representation based on
       the event data described by the event object.

    Args:
      event_object: The event object (instance of EventObject).
      before: Optional number of bytes to include in the output before
              the event. The default is none.
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
      file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          event_object.pathspec)
    except IOError as exception:
      return u'Unable to open file with error: {0:s}'.format(exception)

    offset = getattr(event_object, 'offset', 0)
    if offset - before > 0:
      offset -= before

    file_object = file_entry.GetFileObject()
    file_object.seek(offset, os.SEEK_SET)
    data = file_object.read(int(length) * 16)
    file_object.close()

    return cls.GetHexDump(data, offset)

  @classmethod
  def GetHexDump(cls, data, offset=0):
    """Returns a hexadecimal representation of the contents of a binary string.

    All ASCII characters in the hexadecimal representation (hexdump) are
    translated back to their character representation.

    Args:
      data: The binary string.
      offset: An optional start point in bytes where the data lies, for
              presentation purposes.

    Returns:
      A string that contains the hexadecimal representation of the binary
      string.
    """
    hexdata = binascii.hexlify(data)
    output_strings = []
    # Note that the // statement is a Python specific method of ensuring
    # an integer division.
    hexdata_length = len(hexdata)
    lines_of_hexdata = hexdata_length // 32

    line_number = 0
    point = 0
    while line_number < lines_of_hexdata:
      line_of_hexdata = hexdata[point:point + 32]
      output_strings.append(
          cls.GetHexDumpLine(line_of_hexdata, offset, line_number))
      hexdata_length -= 32
      line_number += 1
      point += 32

    if hexdata_length > 0:
      line_of_hexdata = '{0:s}{1:s}'.format(
          hexdata[point:], ' ' * (32 - hexdata_length))
      output_strings.append(
          cls.GetHexDumpLine(line_of_hexdata, offset, line_number))

    return '\n'.join(output_strings)

  @classmethod
  def GetHexDumpLine(cls, line, orig_ofs, entry_nr=0):
    """Returns a single line of 'xxd'-like hexadecimal representation."""
    output_strings = []
    output_strings.append('{0:07x}: '.format(orig_ofs + entry_nr * 16))

    for bit in range(0, 8):
      output_strings.append('{0:s} '.format(line[bit * 4:bit * 4 + 4]))

    for bit in range(0, 16):
      try:
        data = binascii.unhexlify(line[bit * 2: bit * 2 + 2])
      except TypeError:
        data = '.'

      if ord(data) > 31 and ord(data) < 128:
        output_strings.append(data)
      else:
        output_strings.append('.')

    return ''.join(output_strings)

  @classmethod
  def WriteFile(cls, input_file_object, output_path=None):
    """Writes the data of a file-like object to a "regular" file.

    Args:
      input_file_object: the input file-like object.
      output_path: the path of the output path. The default is None which will
                   write the data to a temporary file.

    Returns:
      The path of the output file.
    """
    if output_path:
      output_file_object = open(output_path, 'wb')
    else:
      output_file_object = tempfile.NamedTemporaryFile()
      output_path = output_file_object.name

    input_file_object.seek(0, os.SEEK_SET)
    data = input_file_object.read(cls.DATA_BUFFER_SIZE)
    while data:
      output_file_object.write(data)
      data = input_file_object.read(cls.DATA_BUFFER_SIZE)

    output_file_object.close()
    return output_path


def FormatHeader(header, char='*'):
  """Formats the header as a line of 80 chars with the header text centered."""
  format_string = '\n{{0:{0:s}^80}}'.format(char)
  return format_string.format(u' {0:s} '.format(header))


def FormatOutputString(name, description, col_length=25):
  """Return a formatted string ready for output."""
  max_width = 80
  line_length = max_width - col_length - 3

  # TODO: add an explanation what this code is doing.
  fmt = u'{{:>{0:d}s}} : {{}}'.format(col_length)
  fmt_second = u'{{:<{0:d}}}{{}}'.format(col_length + 3)

  description = unicode(description)
  if len(description) < line_length:
    return fmt.format(name, description)

  # Split each word up in the description.
  words = description.split()

  current = 0

  lines = []
  word_buffer = []
  for word in words:
    current += len(word) + 1
    if current >= line_length:
      current = len(word)
      lines.append(u' '.join(word_buffer))
      word_buffer = [word]
    else:
      word_buffer.append(word)
  lines.append(u' '.join(word_buffer))

  ret = []
  ret.append(fmt.format(name, lines[0]))
  for line in lines[1:]:
    ret.append(fmt_second.format('', line))

  return u'\n'.join(ret)
