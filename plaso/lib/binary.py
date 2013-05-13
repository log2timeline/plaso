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
"""This file contains a helper library to read binary files."""
import binascii


def ReadUtf16Stream(filehandle, offset=None, eol_char='\x00\x00', byte_size=0):
  """Read an UTF-16 unicode line and returns it.

  Read an UTF-16 encoded line that's terminated by a
  specific end of line character (by default \x00).

  Args:
    filehandle: A file like object to read the data from.
    offset: An offset into the filehandle, if -1 or not set
    the current location into the filehandle is used.
    eol_char: The end of line character.
    byte_size: Size in bytes of the string to be read.

  Returns:
    The UTF 16 string read from the file like object.
  """
  if offset is not None:
    filehandle.seek(offset)

  char_buffer = []

  size_counter = 2
  char_raw = filehandle.read(2)
  while char_raw:
    if byte_size and size_counter >= byte_size:
      break

    if eol_char in char_raw:
      break
    char_buffer.append(char_raw)
    size_counter += 2
    char_raw = filehandle.read(2)

  return ReadUtf16(u''.join(char_buffer))


def ReadUtf16(string_buffer):
  """Return a decoded utf-16 string from a string_buffer."""
  if type(string_buffer) in (list, tuple):
    use_buffer = u''.join(string_buffer)
  else:
    use_buffer = string_buffer

  if not type(use_buffer) in (str, unicode):
    return ''

  try:
    return use_buffer.decode('utf-16').replace('\x00', '')
  except SyntaxError as e:
    logging.error(u'Unable to decode string: {} [{}].'.format(
        HexifyBuffer(string_buffer), e))
  except UnicodeEncodeError as e:
    logging.error(u'Unable to properly decode string: {} [{}]'.format(
        HexifyBuffer(string_buffer), e))

  return u''


def HexifyBuffer(string_buffer):
  """Return a string with the hex representation of a string buffer."""
  chars = []
  for char in string_buffer:
    chars.append(binascii.hexlify(char))

  return u'\\x{}'.format(u'\\x'.join(chars))
