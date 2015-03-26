# -*- coding: utf-8 -*-
"""This file contains utility functions."""

import logging

from plaso.lib import errors
from plaso.lib import lexer


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
  if type(bytes_in) == unicode:
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
  if type(string) != unicode:
    return str(string).decode('utf8', 'ignore')
  return string


class PathReplacer(lexer.Lexer):
  """Replace path variables with values gathered from earlier preprocessing."""

  tokens = [
      lexer.Token('.', '{{([^}]+)}}', 'ReplaceVariable', ''),
      lexer.Token('.', '{([^}]+)}', 'ReplaceString', ''),
      lexer.Token('.', '([^{])', 'ParseString', ''),
      ]

  def __init__(self, pre_obj, data=''):
    """Constructor for a path replacer."""
    super(PathReplacer, self).__init__(data)
    self._path = []
    self._pre_obj = pre_obj

  def GetPath(self):
    """Run the lexer and replace path."""
    while True:
      _ = self.NextToken()
      if self.Empty():
        break

    return u''.join(self._path)

  def ParseString(self, match, **_):
    """Append a string to the path."""
    self._path.append(match.group(1))

  def ReplaceVariable(self, match, **_):
    """Replace a string that should not be a variable."""
    self._path.append(u'{{{0:s}}}'.format(match.group(1)))

  def ReplaceString(self, match, **_):
    """Replace a variable with a given attribute."""
    replace = getattr(self._pre_obj, match.group(1), None)

    if replace:
      self._path.append(replace)
    else:
      raise errors.PathNotFound(
          u'Path variable: {} not discovered yet.'.format(match.group(1)))


def GetInodeValue(inode_raw):
  """Read in a 'raw' inode value and try to convert it into an integer.

  Args:
    inode_raw: A string or an int inode value.

  Returns:
    An integer inode value.
  """
  if type(inode_raw) in (int, long):
    return inode_raw

  if type(inode_raw) is float:
    return int(inode_raw)

  try:
    return int(inode_raw)
  except ValueError:
    # Let's do one more attempt.
    inode_string, _, _ = str(inode_raw).partition('-')
    try:
      return int(inode_string)
    except ValueError:
      return -1
