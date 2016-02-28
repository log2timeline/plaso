# -*- coding: utf-8 -*-
"""This file contains a helper library to read binary files."""

import binascii
import logging
import os

from plaso.lib import py2to3


def ByteArrayCopyToString(byte_array, codepage=u'utf-8'):
  """Copies a UTF-8 encoded byte array into a Unicode string.

  Args:
    byte_array: A byte array containing an UTF-8 encoded string.
    codepage: The codepage of the byte stream.

  Returns:
    A Unicode string.
  """
  byte_stream = b''.join(map(chr, byte_array))
  return ByteStreamCopyToString(byte_stream, codepage=codepage)


def ByteStreamCopyToString(byte_stream, codepage=u'utf-8'):
  """Copies a UTF-8 encoded byte stream into a Unicode string.

  Args:
    byte_stream: A byte stream containing an UTF-8 encoded string.
    codepage: The codepage of the byte stream.

  Returns:
    A Unicode string.
  """
  try:
    string = byte_stream.decode(codepage)
  except UnicodeDecodeError:
    logging.warning(
        u'Unable to decode {0:s} formatted byte stream.'.format(codepage))
    string = byte_stream.decode(codepage, errors='ignore')

  string, _, _ = string.partition(u'\x00')
  return string


def ByteStreamCopyToUTF16Stream(byte_stream, byte_stream_size=None):
  """Reads an UTF-16 formatted stream from a byte stream.

  The UTF-16 formatted stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream: The byte stream that contains the UTF-16 formatted stream.
    byte_stream_size: Optional byte stream size or None if the entire
                      byte stream should be read.

  Returns:
    String containing the UTF-16 formatted stream.
  """
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:
    if (byte_stream[byte_stream_index] == b'\x00' and
        byte_stream[byte_stream_index + 1] == b'\x00'):
      break

    byte_stream_index += 2

  return byte_stream[0:byte_stream_index]


def ReadUTF16Stream(file_object, offset=None, byte_size=0):
  """Reads an UTF-16 formatted stream from a file-like object.

  Reads an UTF-16 formatted stream that's terminated by
  an end-of-string character (\x00\x00) or up to the byte size.

  Args:
    file_object: A file-like object to read the data from.
    offset: An offset into the file object data, if -1 or not set
            the current location into the file object data is used.
    byte_size: Maximum number of bytes to read or 0 if the function
               should keep reading up to the end of file.

  Returns:
    An Unicode string.
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
    byte_stream: The UTF-16 formatted byte stream.
    byte_stream_size: The byte stream size or None if the entire byte stream
                      should be used.

  Returns:
    An Unicode string.
  """
  utf16_stream = ByteStreamCopyToUTF16Stream(
      byte_stream, byte_stream_size=byte_stream_size)

  try:
    return utf16_stream.decode(u'utf-16-le')
  except (UnicodeDecodeError, UnicodeEncodeError) as exception:
    logging.error(u'Unable to decode string: {0:s} with error: {1:s}'.format(
        HexifyBuffer(utf16_stream), exception))

  return utf16_stream.decode(u'utf-16-le', errors=u'ignore')


def ArrayOfUTF16StreamCopyToString(byte_stream, byte_stream_size=None):
  """Copies an array of UTF-16 formatted byte streams to an array of strings.

  The UTF-16 formatted byte stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream: The UTF-16 formatted byte stream.
    byte_stream_size: The byte stream size or None if the entire byte stream
                      should be used.

  Returns:
    An array of Unicode strings.
  """
  array_of_strings = []
  utf16_stream_start = 0
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:
    if (byte_stream[byte_stream_index] == b'\x00' and
        byte_stream[byte_stream_index + 1] == b'\x00'):

      if byte_stream_index - utf16_stream_start <= 2:
        break

      array_of_strings.append(
          byte_stream[utf16_stream_start:byte_stream_index].decode(
              u'utf-16-le'))
      utf16_stream_start = byte_stream_index + 2

    byte_stream_index += 2

  return array_of_strings


def ArrayOfUTF16StreamCopyToStringTable(byte_stream, byte_stream_size=None):
  """Copies an array of UTF-16 formatted byte streams to a string table.

  The string table is a dict of strings with the byte offset as their key.
  The UTF-16 formatted byte stream should be terminated by an end-of-string
  character (\x00\x00). Otherwise the function reads up to the byte stream size.

  Args:
    byte_stream: The UTF-16 formatted byte stream.
    byte_stream_size: The byte stream size or None if the entire byte stream
                      should be used.

  Returns:
    A dict of Unicode strings with the byte offset as their key.
  """
  string_table = {}
  utf16_stream_start = 0
  byte_stream_index = 0
  if not byte_stream_size:
    byte_stream_size = len(byte_stream)

  while byte_stream_index + 1 < byte_stream_size:
    if (byte_stream[byte_stream_index] == b'\x00' and
        byte_stream[byte_stream_index + 1] == b'\x00'):

      if byte_stream_index - utf16_stream_start <= 2:
        break

      string = byte_stream[utf16_stream_start:byte_stream_index].decode(
          u'utf-16-le')
      string_table[utf16_stream_start] = string
      utf16_stream_start = byte_stream_index + 2

    byte_stream_index += 2

  return string_table


def ReadUTF16(string_buffer):
  """Returns a decoded UTF-16 string from a string buffer."""
  if isinstance(string_buffer, (list, tuple)):
    use_buffer = u''.join(string_buffer)
  else:
    use_buffer = string_buffer

  if not isinstance(use_buffer, py2to3.STRING_TYPES):
    return u''

  try:
    return use_buffer.decode(u'utf-16').replace(u'\x00', u'')
  except SyntaxError as exception:
    logging.error(u'Unable to decode string: {0:s} with error: {1:s}.'.format(
        HexifyBuffer(string_buffer), exception))
  except (UnicodeDecodeError, UnicodeEncodeError) as exception:
    logging.error(u'Unable to decode string: {0:s} with error: {1:s}'.format(
        HexifyBuffer(string_buffer), exception))

  return use_buffer.decode(u'utf-16', errors=u'ignore').replace(u'\x00', u'')


def HexifyBuffer(string_buffer):
  """Return a string with the hex representation of a string buffer."""
  chars = []
  for char in string_buffer:
    chars.append(binascii.hexlify(char))

  return u'\\x{0:s}'.format(u'\\x'.join(chars))
