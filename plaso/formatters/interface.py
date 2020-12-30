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

import abc
import re

from plaso.formatters import logger


class EventFormatterHelper(object):
  """Base class of helper for formatting event data."""

  @abc.abstractmethod
  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """


class BooleanEventFormatterHelper(EventFormatterHelper):
  """Helper for formatting boolean event data.

  Attributes:
    input_attribute (str): name of the attribute that contains the boolean
        input value.
    output_attribute (str): name of the attribute where the boolean output
        value should be stored.
    value_if_false (str): output value if the boolean input value is False.
    value_if_true (str): output value if the boolean input value is True.
  """

  def __init__(
      self, input_attribute=None, output_attribute=None, value_if_false=None,
      value_if_true=None):
    """Initialized a helper for formatting boolean event data.

    Args:
      input_attribute (Optional[str]): name of the attribute that contains
          the boolean input value.
      output_attribute (Optional[str]): name of the attribute where the
          boolean output value should be stored.
      value_if_false (str): output value if the boolean input value is False.
      value_if_true (str): output value if the boolean input value is True.
    """
    super(BooleanEventFormatterHelper, self).__init__()
    self.input_attribute = input_attribute
    self.output_attribute = output_attribute
    self.value_if_false = value_if_false
    self.value_if_true = value_if_true

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)
    if input_value:
      output_value = self.value_if_true
    else:
      output_value = self.value_if_false

    event_values[self.output_attribute] = output_value


class EnumerationEventFormatterHelper(EventFormatterHelper):
  """Helper for formatting enumeration event data.

  Attributes:
    default (str): default value.
    input_attribute (str): name of the attribute that contains the enumeration
        input value.
    output_attribute (str): name of the attribute where the enumeration output
        value should be stored.
    values (dict[str, str]): mapping of enumeration input and output values.
  """

  def __init__(
      self, default=None, input_attribute=None, output_attribute=None,
      values=None):
    """Initialized a helper for formatting enumeration event data.

    Args:
      default (Optional[str]): default value.
      input_attribute (Optional[str]): name of the attribute that contains
          the enumeration input value.
      output_attribute (Optional[str]): name of the attribute where the
          enumeration output value should be stored.
      values (Optional[dict[str, str]]): mapping of enumeration input and
          output values.
    """
    super(EnumerationEventFormatterHelper, self).__init__()
    self.default = default
    self.input_attribute = input_attribute
    self.output_attribute = output_attribute
    self.values = values or {}

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    If default value is None and there is no corresponding enumeration value
    then the original value is used.

    Args:
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)

    default_value = self.default
    if default_value is None:
      default_value = input_value

    event_values[self.output_attribute] = self.values.get(
        input_value, default_value)


class FlagsEventFormatterHelper(EventFormatterHelper):
  """Helper for formatting flags event data.

  Attributes:
    input_attribute (str): name of the attribute that contains the flags
        input value.
    output_attribute (str): name of the attribute where the flags output
        value should be stored.
    values (dict[str, str]): mapping of flags input and output values.
  """

  def __init__(
      self, input_attribute=None, output_attribute=None, values=None):
    """Initialized a helper for formatting flags event data.

    Args:
      input_attribute (Optional[str]): name of the attribute that contains
          the flags input value.
      output_attribute (Optional[str]): name of the attribute where the
          flags output value should be stored.
      values (Optional[dict[str, str]]): mapping of flags input and output
          values.
    """
    super(FlagsEventFormatterHelper, self).__init__()
    self.input_attribute = input_attribute
    self.output_attribute = output_attribute
    self.values = values or {}

  def FormatEventValues(self, event_values):
    """Formats event values using the helper.

    Args:
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)

    output_values = []
    for flag, mapped_value in self.values.items():
      if flag & input_value:
        output_values.append(mapped_value)

    event_values[self.output_attribute] = ', '.join(output_values)


class EventFormatter(object):
  """Base class to format event data using a format string.

  Define the (long) format string and the short format string by defining
  FORMAT_STRING and FORMAT_STRING_SHORT. The syntax of the format strings
  is similar to that of format() where the place holder for a certain
  event object attribute is defined as {attribute_name}.

  Attributes:
    helpers (list[EventFormatterHelper]): event formatter helpers.
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
    self.helpers = []

  def _FormatMessage(self, format_string, event_values):
    """Determines the formatted message.

    Args:
      format_string (str): message format string.
      event_values (dict[str, object]): event values.

    Returns:
      str: formatted message.
    """
    if not isinstance(format_string, str):
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
      for attribute, value in event_values.items():
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

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    for helper in self.helpers:
      helper.FormatEventValues(event_values)

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

  def AddHelper(self, helper):
    """Adds an event formatter helper.

    Args:
      helper (EventFormatterHelper): event formatter helper to add.
    """
    self.helpers.append(helper)

  def GetMessage(self, event_values):
    """Determines the message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: message.
    """
    return self._FormatMessage(self.FORMAT_STRING, event_values)

  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """
    if self.FORMAT_STRING_SHORT:
      format_string = self.FORMAT_STRING_SHORT
    else:
      format_string = self.FORMAT_STRING

    short_message_string = self._FormatMessage(format_string, event_values)

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return short_message_string


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

  def _CreateFormatStringMap(
      self, format_string_pieces, format_string_pieces_map):
    """Creates a format string map.

    The format string pieces map is a list containing the attribute name
    per format string piece. E.g. ["Description: {description}"] would be
    mapped to: [0] = "description". If the string piece does not contain
    an attribute name it is treated as text that does not needs formatting.

    Args:
      format_string_pieces (list[str]): format string pieces.
      format_string_pieces_map (list[str]): format string pieces map.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    for format_string_piece in format_string_pieces:
      attribute_names = self._FORMAT_STRING_ATTRIBUTE_NAME_RE.findall(
          format_string_piece)

      if len(set(attribute_names)) > 1:
        raise RuntimeError((
            'Invalid format string piece: [{0:s}] contains more than 1 '
            'attribute name.').format(format_string_piece))

      if not attribute_names:
        # The text format string piece is stored as an empty map entry to keep
        # the index in the map equal to the format string pieces.
        attribute_name = ''

      else:
        attribute_name = attribute_names[0]

      format_string_pieces_map.append(attribute_name)

  def _CreateFormatStringMaps(self):
    """Creates the format string maps.

    Maps are built of the string pieces and their corresponding attribute
    name to optimize conditional string formatting.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    self._format_string_pieces_map = []
    self._CreateFormatStringMap(
        self.FORMAT_STRING_PIECES, self._format_string_pieces_map)

    self._format_string_short_pieces_map = []
    self._CreateFormatStringMap(
        self.FORMAT_STRING_SHORT_PIECES, self._format_string_short_pieces_map)

  def _ConditionalFormatMessage(
      self, format_string_pieces, format_string_pieces_map, event_values):
    """Determines the conditional formatted message.

    Args:
      format_string_pieces (dict[str, str]): format string pieces.
      format_string_pieces_map (list[int, str]): format string pieces map.
      event_values (dict[str, object]): event values.

    Returns:
      str: conditional formatted message.

    Raises:
      RuntimeError: when an invalid format string piece is encountered.
    """
    # Using getattr here to make sure the attribute is not set to None.
    # if A.b = None, hasattr(A, b) is True but getattr(A, b, None) is False.
    string_pieces = []
    for map_index, attribute_name in enumerate(format_string_pieces_map):
      if not attribute_name or attribute_name in event_values:
        if attribute_name:
          attribute = event_values.get(attribute_name, None)
          # If an attribute is an int, yet has zero value we want to include
          # that in the format string, since that is still potentially valid
          # information. Otherwise we would like to skip it.
          if not isinstance(attribute, (bool, float, int)) and not attribute:
            continue

        string_pieces.append(format_string_pieces[map_index])

    format_string = self.FORMAT_STRING_SEPARATOR.join(string_pieces)

    return self._FormatMessage(format_string, event_values)

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

  def GetMessage(self, event_values):
    """Determines the message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: message.
    """
    if not self._format_string_pieces_map:
      self._CreateFormatStringMaps()

    return self._ConditionalFormatMessage(
        self.FORMAT_STRING_PIECES, self._format_string_pieces_map, event_values)

  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """
    if not self._format_string_pieces_map:
      self._CreateFormatStringMaps()

    if (self.FORMAT_STRING_SHORT_PIECES and
        self.FORMAT_STRING_SHORT_PIECES != ['']):
      format_string_pieces = self.FORMAT_STRING_SHORT_PIECES
      format_string_pieces_map = self._format_string_short_pieces_map
    else:
      format_string_pieces = self.FORMAT_STRING_PIECES
      format_string_pieces_map = self._format_string_pieces_map

    short_message_string = self._ConditionalFormatMessage(
        format_string_pieces, format_string_pieces_map, event_values)

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return short_message_string
