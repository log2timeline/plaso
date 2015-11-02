# -*- coding: utf-8 -*-
"""This file contains utility functions."""

import logging
import re


# Illegal Unicode characters for XML.
ILLEGAL_XML_RE = re.compile(
    ur'[\x00-\x08\x0b-\x1f\x7f-\x84\x86-\x9f'
    ur'\ud800-\udfff\ufdd0-\ufddf\ufffe-\uffff]')


def IsText(bytes_in, encoding=None):
  """Examine the bytes in and determine if they are indicative of a text.

  Parsers need quick and at least semi reliable method of discovering whether
  or not a particular byte stream is a text or resembles text or not. This can
  be used in text parsers to determine if a file is a text file or not for
  instance.

  The method assumes the byte sequence is either ASCII, UTF-8, UTF-16 or method
  supplied character encoding. Otherwise it will make the assumption the byte
  sequence is not text, but a byte sequence.

  Args:
    bytes_in: The byte sequence passed to the method that needs examination.
    encoding: Optional encoding to test, if not defined only ASCII, UTF-8 and
    UTF-16 are tried.

  Returns:
    Boolean value indicating whether or not the byte sequence is a text or not.
  """
  # TODO: Improve speed and accuracy of this method.
  # Start with the assumption we are dealing with a text.
  is_ascii = True

  # Check if this is ASCII text string.
  for char in bytes_in:
    if not 31 < ord(char) < 128:
      is_ascii = False
      break

  # We have an ASCII string.
  if is_ascii:
    return is_ascii

  # Is this already a unicode text?
  if isinstance(bytes_in, unicode):
    return True

  # Check if this is UTF-8
  try:
    _ = bytes_in.decode('utf-8')
    return True
  except UnicodeDecodeError:
    pass

  # TODO: UTF 16 decode is successful in too
  # many edge cases where we are not really dealing with
  # a text at all. Leaving this out for now, consider
  # re-enabling or making a better determination.
  #try:
  #  _ = bytes_in.decode('utf-16-le')
  #  return True
  #except UnicodeDecodeError:
  #  pass

  if encoding:
    try:
      _ = bytes_in.decode(encoding)
      return True
    except UnicodeDecodeError:
      pass
    except LookupError:
      logging.error(
          u'String encoding not recognized: {0:s}'.format(encoding))

  return False


def GetUnicodeString(string):
  """Converts the string to Unicode if necessary."""
  if not isinstance(string, unicode):
    return str(string).decode('utf8', 'ignore')
  return string


def RemoveIllegalXMLCharacters(string, replacement=u'\ufffd'):
  """Removes illegal Unicode characters for XML.

  Args:
    string: A string to replace all illegal characters for XML.
    replacement: A replacement character to use in replacement of all
        found illegal characters.

  Return:
    A string where all illegal Unicode characters for XML have been removed.
    If the input is not a string it will be returned unchanged."""
  if isinstance(string, basestring):
    return ILLEGAL_XML_RE.sub(replacement, string)
  return string

