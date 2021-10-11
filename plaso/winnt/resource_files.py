# -*- coding: utf-8 -*-
"""Shared functionality for Windows PE/COFF resource files."""

import re


# Message string specifiers that are considered white space.
_MESSAGE_STRING_WHITE_SPACE_SPECIFIER_RE = re.compile(r'(%[0b]|[\r\n])')

# Message string specifiers that expand to text.
_MESSAGE_STRING_TEXT_SPECIFIER_RE = re.compile(r'%([ .!%nrt])')

# Curly brackets in a message string.
_MESSAGE_STRING_CURLY_BRACKETS = re.compile(r'([\{\}])')

# Message string specifiers that expand to a variable place holder.
_MESSAGE_STRING_PLACE_HOLDER_SPECIFIER_RE = re.compile(
    r'%([1-9][0-9]?)[!]?[s]?[!]?')


def _MessageStringPlaceHolderSpecifierReplacer(match_object):
  """Replaces message string place holders into Python format() style.

  Args:
    match_object (re.Match): regular expression match object.

  Returns:
    str: message string with Python format() style place holders.
  """
  expanded_groups = []

  for group in match_object.groups():
    try:
      place_holder_number = int(group, 10) - 1
      expanded_group = '{{{0:d}:s}}'.format(place_holder_number)
    except ValueError:
      expanded_group = group

    expanded_groups.append(expanded_group)

  return ''.join(expanded_groups)


def FormatMessageStringInPEP3101(message_string):
  """Formats a message string in Python format() (PEP 3101) style.

  Args:
    message_string (str): message string.

  Returns:
    str: message string in Python format() (PEP 3101) style.
  """
  if not message_string:
    return None

  message_string = message_string.rstrip('\0')
  message_string = _MESSAGE_STRING_WHITE_SPACE_SPECIFIER_RE.sub(
      r'', message_string)
  message_string = _MESSAGE_STRING_TEXT_SPECIFIER_RE.sub(
      r'\\\1', message_string)
  message_string = _MESSAGE_STRING_CURLY_BRACKETS.sub(r'\1\1', message_string)
  return _MESSAGE_STRING_PLACE_HOLDER_SPECIFIER_RE.sub(
      _MessageStringPlaceHolderSpecifierReplacer, message_string)
