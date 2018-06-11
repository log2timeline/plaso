# -*- coding: utf-8 -*-
"""This file contains utility functions."""

from __future__ import unicode_literals

import logging

from plaso.lib import py2to3


def IsText(bytes_in, encoding=None):
  """Examine the bytes in and determine if they are indicative of text.

  Parsers need quick and at least semi reliable method of discovering whether
  or not a particular byte stream is text or resembles text or not. This can
  be used in text parsers to determine if a file is a text file or not for
  instance.

  The method assumes the byte sequence is either ASCII, UTF-8, UTF-16 or method
  supplied character encoding. Otherwise it will make the assumption the byte
  sequence is not text, but a byte sequence.

  Args:
    bytes_in (bytes|str): byte stream to examine.
    encoding (Optional[str]): encoding to test, if not defined ASCII and UTF-8
        are tried.

  Returns:
    bool: True if the bytes stream contains text.
  """
  # TODO: Improve speed and accuracy of this method.
  # Start with the assumption we are dealing with text.
  is_text = True

  if isinstance(bytes_in, py2to3.UNICODE_TYPE):
    return is_text

  # Check if this is ASCII text string.
  for value in bytes_in:
    if py2to3.PY_2:
      value = ord(value)
    if not 31 < value < 128:
      is_text = False
      break

  # We have an ASCII string.
  if is_text:
    return is_text

  # Check if this is UTF-8
  try:
    bytes_in.decode('utf-8')
    return True

  except UnicodeDecodeError:
    pass

  if encoding:
    try:
      bytes_in.decode(encoding)
      return True

    except LookupError:
      logging.error('Unsupported encoding: {0:s}'.format(encoding))
    except UnicodeDecodeError:
      pass

  return False
