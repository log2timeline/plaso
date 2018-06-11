# -*- coding: utf-8 -*-
"""This file contains a helper library to read binary files."""

from __future__ import unicode_literals

import codecs
import itertools
import logging
import os

from plaso.lib import py2to3


def ByteArrayCopyToString(byte_array, codepage='utf-8'):
  """Copies a UTF-8 encoded byte array into a Unicode string.

  Args:
    byte_array (bytes): byte stream containing an UTF-8 encoded string.
    codepage (Optional[str]): codepage of the byte stream.

  Returns:
    str: Unicode string.
  """
  byte_stream = b''.join(map(chr, byte_array))
  return ByteStreamCopyToString(byte_stream, codepage=codepage)


def ByteStreamCopyToString(byte_stream, codepage='utf-8'):
  """Copies a UTF-8 encoded byte stream into a Unicode string.

  Args:
    byte_stream (bytes): byte stream containing an UTF-8 encoded string.
    codepage (Optional[str]): codepage of the byte stream.

  Returns:
    str: Unicode string.
  """
  try:
    string = codecs.decode(byte_stream, codepage)
  except UnicodeDecodeError:
    logging.warning(
        'Unable to decode {0:s} formatted byte stream.'.format(codepage))
    string = codecs.decode(byte_stream, codepage, errors='ignore')

  string, _, _ = string.partition('\x00')
  return string


def ByteStreamCopyToUTF16String(byte_stream, byte_stream_size=None):
  """Reads an UTF-16 formatted stream from a byte stream.

  The UTF-16 formatted stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream (bytes): byte stream that contains the UTF-16 formatted
        stream.
    byte_stream_size (Optional[int]): byte stream size or None if the entire
        byte stream should be read.

  Returns:
    bytes: UTF-16 formatted stream.
  """
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:
    if _StreamContainsUTF16NullTerminator(byte_stream, byte_stream_index):
      break

    byte_stream_index += 2

  return byte_stream[0:byte_stream_index]


def ReadUTF16Stream(file_object, offset=None, byte_size=0):
  """Reads an UTF-16 formatted stream from a file-like object.

  Reads an UTF-16 formatted stream that's terminated by
  an end-of-string character (\x00\x00) or up to the byte size.

  Args:
    file_object (file): file-like object to read the data from.
    offset (Optional[int]): offset into the file object data, if -1 or not set
        the current location into the file object data is used.
    byte_size (Optional[int]): maximum number of bytes to read or 0 if the
        function should keep reading up to the end of file.

  Returns:
    str: Unicode string.
  """
  if offset is not None:
    file_object.seek(offset, os.SEEK_SET)

  char_buffer = []

  stream_index = 0
  char_raw = file_object.read(2)
  while char_raw:
    if byte_size and stream_index >= byte_size:
      break

    if b'\x00\x00' in char_raw:
      break
    char_buffer.append(char_raw)
    stream_index += 2
    char_raw = file_object.read(2)

  return ReadUTF16(b''.join(char_buffer))


def UTF16StreamCopyToString(byte_stream, byte_stream_size=None):
  """Copies an UTF-16 formatted byte stream to a string.

  The UTF-16 formatted byte stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream (bytes): UTF-16 formatted byte stream.
    byte_stream_size (Optional[int]): byte stream size or None if the entire
        byte stream should be used.

  Returns:
    str: Unicode string.
  """
  utf16_stream = ByteStreamCopyToUTF16String(
      byte_stream, byte_stream_size=byte_stream_size)

  try:
    string = codecs.decode(utf16_stream, 'utf-16-le')
    return string
  except (UnicodeDecodeError, UnicodeEncodeError) as exception:
    logging.error('Unable to decode string: {0:s} with error: {1!s}'.format(
        HexifyBuffer(utf16_stream), exception))

  return utf16_stream.decode('utf-16-le', errors='ignore')


def ArrayOfUTF16StreamCopyToString(byte_stream, byte_stream_size=None):
  """Copies an array of UTF-16 formatted byte streams to an array of strings.

  The UTF-16 formatted byte stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream (str): UTF-16 formatted byte stream.
    byte_stream_size (Optional[int]): byte stream size or None if the entire
        byte stream should be used.

  Returns:
    list[str]: Unicode strings.
  """
  array_of_strings = []
  utf16_stream_start = 0
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:
    if _StreamContainsUTF16NullTerminator(byte_stream, byte_stream_index):
      if byte_stream_index - utf16_stream_start <= 2:
        break

      utf16_stream = byte_stream[utf16_stream_start:byte_stream_index]
      string = codecs.decode(utf16_stream, 'utf-16-le')
      array_of_strings.append(string)
      utf16_stream_start = byte_stream_index + 2

    byte_stream_index += 2

  return array_of_strings


def ArrayOfUTF16StreamCopyToStringTable(byte_stream, byte_stream_size=None):
  """Copies an array of UTF-16 formatted byte streams to a string table.

  The string table is a dict of strings with the byte offset as their key.
  The UTF-16 formatted byte stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream (bytes): The UTF-16 formatted byte stream.
    byte_stream_size (int): The byte stream size or None if the entire byte
      stream should be used.

  Returns:
    dict[int, str]: Unicode strings with their offset in the byte stream as
        their key.
  """
  string_table = {}
  utf16_stream_start = 0
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:

    if _StreamContainsUTF16NullTerminator(byte_stream, byte_stream_index):
      if byte_stream_index - utf16_stream_start <= 2:
        break

      utf16_stream = byte_stream[utf16_stream_start:byte_stream_index]
      string = codecs.decode(utf16_stream, 'utf-16-le')
      string_table[utf16_stream_start] = string
      utf16_stream_start = byte_stream_index + 2

    byte_stream_index += 2

  return string_table


def ReadUTF16(string_buffer):
  """Returns a decoded UTF-16 string from a string buffer.

  Args:
    string_buffer(bytes): byte string.

  Returns:
    str: Unicode string.
  """
  if isinstance(string_buffer, (list, tuple)):
    use_buffer = ''.join(string_buffer)
  else:
    use_buffer = string_buffer

  if not isinstance(use_buffer, py2to3.BYTES_TYPE):
    return ''

  try:
    return codecs.decode(use_buffer, 'utf-16').replace('\x00', '')
  except SyntaxError as exception:
    logging.error('Unable to decode string: {0:s} with error: {1!s}.'.format(
        HexifyBuffer(string_buffer), exception))
  except (UnicodeDecodeError, UnicodeEncodeError) as exception:
    logging.error('Unable to decode string: {0:s} with error: {1!s}'.format(
        HexifyBuffer(string_buffer), exception))

  return codecs.decode(
      use_buffer, 'utf-16', errors='ignore').replace('\x00', '')


def HexifyBuffer(byte_sequence):
  """Returns an hexadecimal representation of a byte sequence.

  Args:
    byte_sequence (bytes): byte sequence.

  Returns:
    str: hexadecimal representation of the byte stream.
  """
  hex_bytes = codecs.encode(byte_sequence, 'hex')
  output_string = codecs.decode(hex_bytes, 'utf-8')
  string_iterators = [iter(output_string)] * 2

  # pylint: disable=no-member
  if py2to3.PY_2:
    iterators = itertools.izip_longest(*string_iterators)
  else:
    iterators = itertools.zip_longest(*string_iterators)
  groups = list(iterators)
  output_string = ''.join(
      ['\\x{0:s}{1:s}'.format(group[0], group[1]) for group in groups])
  return output_string


def _StreamContainsUTF16NullTerminator(byte_stream, offset):
  """Checks if the given byte stream has a UTF-16 null character at the offset.

  This is a little complicated because of the necessity of supporting Python 2
  and 3.

  Args:
    byte_stream (bytes): byte string.
    offset (int): byte stream offset to check.

  Returns:
    bool: whether there's a UTF-16 null terminator in the stream at the given
        offset.
  """
  byte_1 = byte_stream[offset]
  byte_2 = byte_stream[offset + 1]
  if py2to3.PY_2 and byte_1 == b'\x00' and byte_2 == b'\x00':
    return True
  if py2to3.PY_3 and byte_1 == 0 and byte_2 == 0:
    return True
  return False
