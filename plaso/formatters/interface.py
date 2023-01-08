# -*- coding: utf-8 -*-
"""This file contains the event formatters interface classes.

The l2t_csv and other formats are dependent on a message field,
referred to as description_long and description_short in l2t_csv.

Plaso no longer stores these field explicitly.

A formatter, with a format string definition, is used to convert
the event object values into a formatted string that is similar
to the description_long and description_short field.
"""

import abc
import re

from plaso.formatters import logger


class EventFormatterHelper(object):
  """Base class of helper for formatting event data."""

  @abc.abstractmethod
  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
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

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)
    if input_value:
      output_value = self.value_if_true
    else:
      output_value = self.value_if_false

    event_values[self.output_attribute] = output_value


class CustomEventFormatterHelper(EventFormatterHelper):
  """Base class for a helper for custom formatting of event data."""

  DATA_TYPE = ''
  IDENTIFIER = ''

  @abc.abstractmethod
  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """


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

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    If default value is None and there is no corresponding enumeration value
    then the original value is used.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)
    if input_value is not None:
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

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    input_value = event_values.get(self.input_attribute, None)
    if input_value is None:
      return

    output_values = []
    for flag, mapped_value in self.values.items():
      if flag & input_value:
        output_values.append(mapped_value)

    event_values[self.output_attribute] = ', '.join(output_values)


class EventFormatter(object):
  """Base class to format event values.

  Attributes:
    custom_helpers (list[str]): identifiers of custom event formatter helpers.
    helpers (list[EventFormatterHelper]): event formatter helpers.
    source_mapping (tuple[str, str]): short and (long) source mapping.
  """

  # The format string can be defined as:
  # {name}, {name:format}, {name!conversion}, {name!conversion:format}
  _FORMAT_STRING_ATTRIBUTE_NAME_RE = re.compile(
      '{([a-z][a-zA-Z0-9_]*)[!]?[^:}]*[:]?[^}]*}')

  def __init__(self, data_type='internal'):
    """Initializes an event formatter.

    Args:
      data_type (Optional[str]): unique identifier for the event data supported
          by the formatter.
    """
    super(EventFormatter, self).__init__()
    self._data_type = data_type
    self._format_string_attribute_names = None

    self.custom_helpers = []
    self.helpers = []
    self.source_mapping = None

  @property
  def data_type(self):
    """str: unique identifier for the event data supported by the formatter."""
    return self._data_type.lower()

  def _FormatMessage(self, format_string, event_values):
    """Determines the formatted message.

    Args:
      format_string (str): message format string.
      event_values (dict[str, object]): event values.

    Returns:
      str: formatted message.
    """
    try:
      message_string = format_string.format(**event_values)

    except KeyError as exception:
      data_type = event_values.get('data_type', 'N/A')
      display_name = event_values.get('display_name', 'N/A')
      event_identifier = event_values.get('uuid', 'N/A')

      parser_chain = event_values.get('_parser_chain', None)
      if not parser_chain:
        # Note that parser is kept for backwards compatibility.
        parser_chain = event_values.get('parser', None) or 'N/A'

      error_message = (
          'unable to format string: "{0:s}" missing required event '
          'value: {1!s}').format(format_string, exception)
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

      parser_chain = event_values.get('_parser_chain', None)
      if not parser_chain:
        # Note that parser is kept for backwards compatibility.
        parser_chain = event_values.get('parser', None) or 'N/A'

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

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    for helper in self.helpers:
      helper.FormatEventValues(output_mediator, event_values)

  @abc.abstractmethod
  def GetFormatStringAttributeNames(self):
    """Retrieves the attribute names in the format string.

    Returns:
      set(str): attribute names.
    """

  # pylint: disable=unused-argument
  def AddCustomHelper(
      self, identifier, input_attribute=None, output_attribute=None):
    """Adds a custom event formatter helper.

    Args:
      identifier (str): identifier.
      input_attribute (Optional[str]): name of the attribute that contains
          the input value.
      output_attribute (Optional[str]): name of the attribute where the
          output value should be stored.
    """
    self.custom_helpers.append(identifier)

  def AddHelper(self, helper):
    """Adds an event formatter helper.

    Args:
      helper (EventFormatterHelper): event formatter helper to add.
    """
    self.helpers.append(helper)

  @abc.abstractmethod
  def GetMessage(self, event_values):
    """Determines the message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: message.
    """

  @abc.abstractmethod
  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """


class BasicEventFormatter(EventFormatter):
  """Format event values using a message format string.

  Attributes:
    custom_helpers (list[str]): identifiers of custom event formatter helpers.
    helpers (list[EventFormatterHelper]): event formatter helpers.
  """

  def __init__(
      self, data_type='basic', format_string=None, format_string_short=None):
    """Initializes a basic event formatter.

    The syntax of the format strings is similar to that of format() where
    the place holder for a certain event object attribute is defined as
    {attribute_name}.

    Args:
      data_type (Optional[str]): unique identifier for the event data supported
          by the formatter.
      format_string (Optional[str]): (long) message format string.
      format_string_short (Optional[str]): short message format string.
    """
    super(BasicEventFormatter, self).__init__(data_type=data_type)
    self._format_string_attribute_names = None
    self._format_string = format_string
    self._format_string_short = format_string_short

  def GetFormatStringAttributeNames(self):
    """Retrieves the attribute names in the format string.

    Returns:
      set(str): attribute names.
    """
    if self._format_string_attribute_names is None:
      self._format_string_attribute_names = (
          self._FORMAT_STRING_ATTRIBUTE_NAME_RE.findall(
              self._format_string))

    return set(self._format_string_attribute_names)

  def GetMessage(self, event_values):
    """Determines the message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: message.
    """
    return self._FormatMessage(self._format_string, event_values)

  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """
    if self._format_string_short:
      format_string = self._format_string_short
    else:
      format_string = self._format_string

    short_message_string = self._FormatMessage(format_string, event_values)

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return short_message_string


class ConditionalEventFormatter(EventFormatter):
  """Conditionally format event values using format string pieces."""

  _DEFAULT_FORMAT_STRING_SEPARATOR = ' '

  def __init__(
      self, data_type='conditional', format_string_pieces=None,
      format_string_separator=None, format_string_short_pieces=None):
    """Initializes a conditional event formatter.

    The syntax of the format strings pieces is similar to of the basic event
    formatter (BasicEventFormatter). Every format string piece should contain
    at maximum one unique attribute name. Format string pieces without an
    attribute name are supported.

    Args:
      data_type (Optional[str]): unique identifier for the event data supported
          by the formatter.
      format_string_pieces (Optional[list[str]]): (long) message format string
          pieces.
      format_string_separator (Optional[str]): string by which separate format
          string pieces should be joined.
      format_string_short_pieces (Optional[list[str]]): short message format
          string pieces.
    """
    if format_string_separator is None:
      format_string_separator = self._DEFAULT_FORMAT_STRING_SEPARATOR

    super(ConditionalEventFormatter, self).__init__(data_type=data_type)
    self._format_string_pieces = format_string_pieces or []
    self._format_string_pieces_map = []
    self._format_string_separator = format_string_separator
    self._format_string_short_pieces = format_string_short_pieces or []
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
        self._format_string_pieces, self._format_string_pieces_map)

    self._format_string_short_pieces_map = []
    self._CreateFormatStringMap(
        self._format_string_short_pieces, self._format_string_short_pieces_map)

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
    string_pieces = []
    for map_index, attribute_name in enumerate(format_string_pieces_map):
      if not attribute_name or event_values.get(
          attribute_name, None) is not None:
        string_pieces.append(format_string_pieces[map_index])

    format_string = self._format_string_separator.join(string_pieces)
    return self._FormatMessage(format_string, event_values)

  def GetFormatStringAttributeNames(self):
    """Retrieves the attribute names in the format string.

    Returns:
      set(str): attribute names.
    """
    if self._format_string_attribute_names is None:
      self._format_string_attribute_names = []
      for format_string_piece in self._format_string_pieces:
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
        self._format_string_pieces, self._format_string_pieces_map,
        event_values)

  def GetMessageShort(self, event_values):
    """Determines the short message.

    Args:
      event_values (dict[str, object]): event values.

    Returns:
      str: short message.
    """
    if not self._format_string_pieces_map:
      self._CreateFormatStringMaps()

    if (self._format_string_short_pieces and
        self._format_string_short_pieces != ['']):
      format_string_pieces = self._format_string_short_pieces
      format_string_pieces_map = self._format_string_short_pieces_map
    else:
      format_string_pieces = self._format_string_pieces
      format_string_pieces_map = self._format_string_pieces_map

    short_message_string = self._ConditionalFormatMessage(
        format_string_pieces, format_string_pieces_map, event_values)

    # Truncate the short message string if necessary.
    if len(short_message_string) > 80:
      short_message_string = '{0:s}...'.format(short_message_string[:77])

    return short_message_string
