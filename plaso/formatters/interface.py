# -*- coding: utf-8 -*-
"""This file contains the event formatters interface classes.

The l2t_csv and other formats are dependent on a message field,
referred to as description_long and description_short in l2t_csv.

Plaso no longer stores these field explicitly.

A formatter, with a format string definition, is used to convert
the event object values into a formatted string that is similar
to the description_long and description_short field.
"""

from __future__ import unicode_literals

import re

from plaso.formatters import logger
from plaso.lib import errors
from plaso.lib import py2to3


class EventFormatter(object):
  """Base class to format event type specific data using a format string.

  Define the (long) format string and the short format string by defining
  FORMAT_STRING and FORMAT_STRING_SHORT. The syntax of the format strings
  is similar to that of format() where the place holder for a certain
  event object attribute is defined as {attribute_name}.
  """

  # The data type is a unique identifier for the event data. The current
  # approach is to define it as human readable string in the format
  # root:branch: ... :leaf, e.g. a page visited entry inside a Chrome History
  # database is defined as: chrome:history:page_visited.
  DATA_TYPE = 'internal'

  # The format string.
  FORMAT_STRING = ''
  FORMAT_STRING_SHORT = ''

  # The source short and long strings.
  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = ''

  # The format string can be defined as:
  # {name}, {name:format}, {name!conversion}, {name!conversion:format}
  _FORMAT_STRING_ATTRIBUTE_NAME_RE = re.compile(
      '{([a-z][a-zA-Z0-9_]*)[!]?[^:}]*[:]?[^}]*}')

  def __init__(self):
    """Initializes an event formatter object."""
    super(EventFormatter, self).__init__()
    self._format_string_attribute_names = None

  def _FormatMessage(self, format_string, event_values):
    """Determines the formatted message string.

    Args:
      format_string (str): message format string.
      event_values (dict[str, object]): event values.

    Returns:
      str: formatted message string.
    """
    if not isinstance(format_string, py2to3.UNICODE_TYPE):
      logger.warning('Format string: {0:s} is non-Unicode.'.format(
          format_string))

      # Plaso code files should be in UTF-8 any thus binary strings are
      # assumed UTF-8. If this is not the case this should be fixed.
      format_string = format_string.decode('utf-8', errors='ignore')

    try:
      message_string = format_string.format(**event_values)

    except KeyError as exception:
      data_type = event_values.get('data_type', 'N/A')
      display_name = event_values.get('display_name', 'N/A')
      event_identifier = event_values.get('uuid', 'N/A')
      parser_chain = event_values.get('parser', 'N/A')

      error_message = (
          'unable to format string: "{0:s}" event object is missing required '
          'attributes: {1!s}').format(format_string, exception)
      error_message = (
          'Event: {0:s} data type: {1:s} display name: {2:s} '
          'parser chain: {3:s} with error: {4:s}').format(
              event_identifier, data_type, display_name, parser_chain,
              error_message)
      logger.error(error_message)

      attribute_values = []
      for attribute, value in iter(event_values.items()):
        attribute_values.append('{0:s}: {1!s}'.format(attribute, value))

      message_string = ' '.join(attribute_values)

    except UnicodeDecodeError as exception:
      data_type = event_values.get('data_type', 'N/A')
      display_name = event_values.get('display_name', 'N/A')
      event_identifier = event_values.get('uuid', 'N/A')
      parser_chain = event_values.get('parser', 'N/A')

      error_message = 'Unicode decode error: {0!s}'.format(exception)
      error_message = (
          'Event: {0:s} data type: {1:s} display name: {2:s} '
          'parser chain: {3:s} with error: {4:s}').format(
              event_identifier, data_type, display_name, parser_chain,
              error_message)
      logger.error(error_message)

      message_string = ''

    # Strip carriage return and linefeed form the message strings.
    # Using replace function here because it is faster than re.sub() or
    # string.strip().
    return message_string.replace('\r', '').replace('\n', '')

  def _FormatMessages(self, format_string, short_format_string, event_values):
    """Determines the formatted message strings.

    Args:
      format_string (str): message format string.
      short_format_string (str): short message format string.
      event_values (dict[str, object]): event values.

    Returns:
      tuple(str, str): formatted message string and short message string.
    """
    message_string = self._FormatMessage(format_string, event_values)

    if short_format_string:
      short_message_string = self._FormatMessage(
          short_format_string, event_values)
    else:
      short_message_string = message_string

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return message_string, short_message_string

  def GetFormatStringAttributeNames(self):
    """Retrieves the attribute names in the format string.

    Returns:
      set(str): attribute names.
    """
    if self._format_string_attribute_names is None:
      self._format_string_attribute_names = (
          self._FORMAT_STRING_ATTRIBUTE_NAME_RE.findall(
              self.FORMAT_STRING))

    return set(self._format_string_attribute_names)

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()
    return self._FormatMessages(
        self.FORMAT_STRING, self.FORMAT_STRING_SHORT, event_values)

  # pylint: disable=unused-argument
  def GetSources(self, event, event_data):
    """Determines the the short and long source for an event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): short and long source string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    return self.SOURCE_SHORT, self.SOURCE_LONG


class ConditionalEventFormatter(EventFormatter):
  """Base class to conditionally format event data using format string pieces.

  Define the (long) format string and the short format string by defining
  FORMAT_STRING_PIECES and FORMAT_STRING_SHORT_PIECES. The syntax of the
  format strings pieces is similar to of the event formatter
  (EventFormatter). Every format string piece should contain a single
  attribute name or none.

  FORMAT_STRING_SEPARATOR is used to control the string which the separate
  string pieces should be joined. It contains a space by default.
  """
  # The format string pieces.
  FORMAT_STRING_PIECES = ['']
  FORMAT_STRING_SHORT_PIECES = ['']

  # The separator used to join the string pieces.
  FORMAT_STRING_SEPARATOR = ' '

  def __init__(self):
    """Initializes the conditional formatter."""
    super(ConditionalEventFormatter, self).__init__()
    self._format_string_pieces_map = []
    self._format_string_short_pieces_map = []

  def _CreateFormatStringMaps(self):
    """Creates the format string maps.

    Maps are built of the string pieces and their corresponding attribute
    name to optimize conditional string formatting.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    # The format string can be defined as:
    # {name}, {name:format}, {name!conversion}, {name!conversion:format}
    regexp = re.compile('{[a-z][a-zA-Z0-9_]*[!]?[^:}]*[:]?[^}]*}')
    regexp_name = re.compile('[a-z][a-zA-Z0-9_]*')

    # The format string pieces map is a list containing the attribute name
    # per format string piece. E.g. ["Description: {description}"] would be
    # mapped to: [0] = "description". If the string piece does not contain
    # an attribute name it is treated as text that does not needs formatting.
    self._format_string_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            'Invalid format string piece: [{0:s}] contains more than 1 '
            'attribute name.').format(format_string_piece))

    self._format_string_short_pieces_map = []
    for format_string_piece in self.FORMAT_STRING_SHORT_PIECES:
      result = regexp.findall(format_string_piece)
      if not result:
        # The text format string piece is stored as an empty map entry to
        # keep the index in the map equal to the format string pieces.
        self._format_string_short_pieces_map.append('')
      elif len(result) == 1:
        # Extract the attribute name.
        attribute_name = regexp_name.findall(result[0])[0]
        self._format_string_short_pieces_map.append(attribute_name)
      else:
        raise RuntimeError((
            'Invalid short format string piece: [{0:s}] contains more '
            'than 1 attribute name.').format(format_string_piece))

  def _ConditionalFormatMessages(self, event_values):
    """Determines the conditional formatted message strings.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    if not self._format_string_pieces_map:
      self._CreateFormatStringMaps()

    # Using getattr here to make sure the attribute is not set to None.
    # if A.b = None, hasattr(A, b) is True but getattr(A, b, None) is False.
    string_pieces = []
    for map_index, attribute_name in enumerate(self._format_string_pieces_map):
      if not attribute_name or attribute_name in event_values:
        if attribute_name:
          attribute = event_values.get(attribute_name, None)
          # If an attribute is an int, yet has zero value we want to include
          # that in the format string, since that is still potentially valid
          # information. Otherwise we would like to skip it.
          # pylint: disable=unidiomatic-typecheck
          if (not isinstance(attribute, (bool, float)) and
              not isinstance(attribute, py2to3.INTEGER_TYPES) and
              not attribute):
            continue

        string_pieces.append(self.FORMAT_STRING_PIECES[map_index])

    format_string = self.FORMAT_STRING_SEPARATOR.join(string_pieces)

    string_pieces = []
    for map_index, attribute_name in enumerate(
        self._format_string_short_pieces_map):
      if not attribute_name or event_values.get(attribute_name, None):
        string_pieces.append(self.FORMAT_STRING_SHORT_PIECES[map_index])
    short_format_string = self.FORMAT_STRING_SEPARATOR.join(string_pieces)

    return self._FormatMessages(
        format_string, short_format_string, event_values)

  def GetFormatStringAttributeNames(self):
    """Retrieves the attribute names in the format string.

    Returns:
      set(str): attribute names.
    """
    if self._format_string_attribute_names is None:
      self._format_string_attribute_names = []
      for format_string_piece in self.FORMAT_STRING_PIECES:
        attribute_names = self._FORMAT_STRING_ATTRIBUTE_NAME_RE.findall(
            format_string_piece)

        if attribute_names:
          self._format_string_attribute_names.extend(attribute_names)

    return set(self._format_string_attribute_names)

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()
    return self._ConditionalFormatMessages(event_values)
