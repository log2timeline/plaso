# -*- coding: utf-8 -*-
"""YAML-based formatters file."""

import yaml

from plaso.formatters import interface
from plaso.lib import errors


class YAMLFormattersFile(object):
  """YAML-based formatters file.

  A YAML-based formatters file contains one or more event formatter
  definitions. An event formatter definition consists of:

  type: 'conditional'
  data_type: 'fs:stat'
  message:
  - '{display_name}'
  - 'Type: {file_entry_type}'
  - '({unallocated})'
  short_message:
  - '{filename}'
  short_source: 'FILE'
  source: 'File stat'

  Where:
  * type, defines the formatter data type, which can be "basic" or
    "conditional";
  * data_type, defines the corresponding event data type;
  * message, defines a list of message string pieces;
  * separator, defines the message and short message string pieces separator;
  * short_message, defines the short message string pieces;
  * short_source, defines the short source description;
  * source, defines the source description.
  """

  _SUPPORTED_KEYS = frozenset([
      'data_type',
      'boolean_helpers',
      'custom_helpers',
      'enumeration_helpers',
      'flags_helpers',
      'message',
      'separator',
      'short_message',
      'short_source',
      'source',
      'type'])

  def _ReadBooleanHelpers(self, formatter, boolean_helpers_definition_values):
    """Reads boolean helper definitions from a list.

    Args:
      formatter (EventFormatter): an event formatter.
      boolean_helpers_definition_values (list[dict[str, object]]):
          boolean helpers definition values.

    Raises:
      ParseError: if the format of the boolean helper definitions are incorrect.
    """
    for boolean_helper in boolean_helpers_definition_values:
      input_attribute = boolean_helper.get('input_attribute', None)
      if not input_attribute:
        raise errors.ParseError(
            'Invalid boolean helper missing input attribute.')

      output_attribute = boolean_helper.get('output_attribute', None)
      if not output_attribute:
        raise errors.ParseError(
            'Invalid boolean helper missing output attribute.')

      value_if_false = boolean_helper.get('value_if_false', None)
      value_if_true = boolean_helper.get('value_if_true', None)

      helper = interface.BooleanEventFormatterHelper(
          input_attribute=input_attribute, output_attribute=output_attribute,
          value_if_false=value_if_false, value_if_true=value_if_true)

      formatter.AddHelper(helper)

  def _ReadCustomHelpers(self, formatter, custom_helpers_definition_values):
    """Reads custom helper definitions from a list.

    Args:
      formatter (EventFormatter): an event formatter.
      custom_helpers_definition_values (list[dict[str, object]]):
          custom helpers definition values.

    Raises:
      ParseError: if the format of the custom helper definitions are incorrect.
    """
    for custom_helper in custom_helpers_definition_values:
      identifier = custom_helper.get('identifier', None)
      if not identifier:
        raise errors.ParseError(
            'Invalid custom helper missing identifier.')

      input_attribute = custom_helper.get('input_attribute', None)
      output_attribute = custom_helper.get('output_attribute', None)

      formatter.AddCustomHelper(
          identifier, input_attribute=input_attribute,
          output_attribute=output_attribute)

  def _ReadEnumerationHelpers(
      self, formatter, enumeration_helpers_definition_values):
    """Reads enumeration helper definitions from a list.

    Args:
      formatter (EventFormatter): an event formatter.
      enumeration_helpers_definition_values (list[dict[str, object]]):
          enumeration helpers definition values.

    Raises:
      ParseError: if the format of the enumeration helper definitions are
          incorrect.
    """
    for enumeration_helper in enumeration_helpers_definition_values:
      input_attribute = enumeration_helper.get('input_attribute', None)
      if not input_attribute:
        raise errors.ParseError(
            'Invalid enumeration helper missing input attribute.')

      output_attribute = enumeration_helper.get('output_attribute', None)
      if not output_attribute:
        raise errors.ParseError(
            'Invalid enumeration helper missing output attribute.')

      values = enumeration_helper.get('values', None)
      if not values:
        raise errors.ParseError('Invalid enumeration helper missing values.')

      default_value = enumeration_helper.get('default_value', None)

      helper = interface.EnumerationEventFormatterHelper(
          default=default_value, input_attribute=input_attribute,
          output_attribute=output_attribute, values=values)

      formatter.AddHelper(helper)

  def _ReadFlagsHelpers(self, formatter, flags_helpers_definition_values):
    """Reads flags helper definitions from a list.

    Args:
      formatter (EventFormatter): an event formatter.
      flags_helpers_definition_values (list[dict[str, object]]): flags helpers
          definition values.

    Raises:
      ParseError: if the format of the flags helper definitions are incorrect.
    """
    for flags_helper in flags_helpers_definition_values:
      input_attribute = flags_helper.get('input_attribute', None)
      if not input_attribute:
        raise errors.ParseError(
            'Invalid flags helper missing input attribute.')

      output_attribute = flags_helper.get('output_attribute', None)
      if not output_attribute:
        raise errors.ParseError(
            'Invalid flags helper missing output attribute.')

      values = flags_helper.get('values', None)
      if not values:
        raise errors.ParseError('Invalid flags helper missing values.')

      helper = interface.FlagsEventFormatterHelper(
          input_attribute=input_attribute, output_attribute=output_attribute,
          values=values)

      formatter.AddHelper(helper)

  def _ReadFormatterDefinition(self, formatter_definition_values):
    """Reads an event formatter definition from a dictionary.

    Args:
      formatter_definition_values (dict[str, object]): formatter definition
          values.

    Returns:
      EventFormatter: an event formatter.

    Raises:
      ParseError: if the format of the formatter definition is not set
          or incorrect.
    """
    if not formatter_definition_values:
      raise errors.ParseError('Missing formatter definition values.')

    different_keys = set(formatter_definition_values) - self._SUPPORTED_KEYS
    if different_keys:
      different_keys = ', '.join(different_keys)
      raise errors.ParseError('Undefined keys: {0:s}'.format(different_keys))

    formatter_type = formatter_definition_values.get('type', None)
    if not formatter_type:
      raise errors.ParseError(
          'Invalid event formatter definition missing type.')

    if formatter_type not in ('basic', 'conditional'):
      raise errors.ParseError(
          'Invalid event formatter definition unsupported type: {0!s}.'.format(
              formatter_type))

    data_type = formatter_definition_values.get('data_type', None)
    if not data_type:
      raise errors.ParseError(
          'Invalid event formatter definition missing data type.')

    message = formatter_definition_values.get('message', None)
    if not message:
      raise errors.ParseError(
          'Invalid event formatter definition: {0:s} missing message.'.format(
              data_type))

    short_message = formatter_definition_values.get('short_message', None)
    if not short_message:
      raise errors.ParseError((
          'Invalid event formatter definition: {0:s} missing short '
          'message.').format(data_type))

    short_source = formatter_definition_values.get('short_source', None)
    if not short_source:
      raise errors.ParseError((
          'Invalid event formatter definition: {0:s} missing short '
          'source.').format(data_type))

    source = formatter_definition_values.get('source', None)
    if not source:
      raise errors.ParseError(
          'Invalid event formatter definition: {0:s} missing source.'.format(
              data_type))

    if formatter_type == 'basic':
      formatter = interface.BasicEventFormatter(
          data_type=data_type, format_string=message,
          format_string_short=short_message)

    elif formatter_type == 'conditional':
      separator = formatter_definition_values.get('separator', None)
      formatter = interface.ConditionalEventFormatter(
          data_type=data_type, format_string_pieces=message,
          format_string_separator=separator,
          format_string_short_pieces=short_message)

    boolean_helpers = formatter_definition_values.get('boolean_helpers', [])
    self._ReadBooleanHelpers(formatter, boolean_helpers)

    custom_helpers = formatter_definition_values.get('custom_helpers', [])
    self._ReadCustomHelpers(formatter, custom_helpers)

    enumeration_helpers = formatter_definition_values.get(
        'enumeration_helpers', [])
    self._ReadEnumerationHelpers(formatter, enumeration_helpers)

    flags_helpers = formatter_definition_values.get('flags_helpers', [])
    self._ReadFlagsHelpers(formatter, flags_helpers)

    if short_source and source:
      formatter.source_mapping = (short_source, source)

    return formatter

  def _ReadFromFileObject(self, file_object):
    """Reads the event formatters from a file-like object.

    Args:
      file_object (file): formatters file-like object.

    Yields:
      EventFormatter: an event formatter.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_definition in yaml_generator:
      yield self._ReadFormatterDefinition(yaml_definition)

  def ReadFromFile(self, path):
    """Reads the event formatters from a YAML file.

    Args:
      path (str): path to a formatters file.

    Yields:
      EventFormatter: an event formatter.
    """
    with open(path, 'r', encoding='utf-8') as file_object:
      for yaml_definition in self._ReadFromFileObject(file_object):
        yield yaml_definition
