# -*- coding: utf-8 -*-
"""YAML-based formatters file."""

from __future__ import unicode_literals

import io
import yaml

from plaso.formatters import interface
from plaso.lib import errors


class YAMLFormattersFile(object):
  """YAML-based formatters file.

  A YAML-based formatters file contains one or more event formatters.
  type: 'conditional'
  data_type: 'fs:stat'
  message:
  - '{display_name}'
  - 'Type: {file_entry_type}'
  - '({unallocated})'
  short_message:
  - '{filename}'
  short_source: 'FILE'
  source: 'File system'

  Where:
  * type, defines the formatter data type, which can be "basic" or
    "conditional";
  * data_type, defines the corresponding event data type;
  * message, defines a list of message string pieces;
  * short_message, defines the short message string pieces;
  * short_source, defines the short source;
  * source, defines the source.
  """

  _SUPPORTED_KEYS = frozenset([
      'data_type',
      'message',
      'short_message',
      'short_source',
      'source',
      'type'])

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
          'Invalid event formatter definition missing message.')

    short_message = formatter_definition_values.get('short_message', None)
    if not short_message:
      raise errors.ParseError(
          'Invalid event formatter definition missing short message.')

    short_source = formatter_definition_values.get('short_source', None)
    if not short_source:
      raise errors.ParseError(
          'Invalid event formatter definition missing short source.')

    source = formatter_definition_values.get('source', None)
    if not source:
      raise errors.ParseError(
          'Invalid event formatter definition missing source.')

    if formatter_type == 'basic':
      formatter = interface.EventFormatter()
      # TODO: check if message and short_message are strings
      formatter.FORMAT_STRING = message
      formatter.FORMAT_STRING_SHORT = short_message

    elif formatter_type == 'conditional':
      formatter = interface.ConditionalEventFormatter()
      # TODO: check if message and short_message are list of strings
      formatter.FORMAT_STRING_PIECES = message
      formatter.FORMAT_STRING_SHORT_PIECES = short_message

    formatter.DATA_TYPE = data_type
    formatter.SOURCE_LONG = source
    formatter.SOURCE_SHORT = short_source

    return formatter

  def _ReadFromFileObject(self, file_object):
    """Reads the event formatters from a file-like object.

    Args:
      file_object (file): formatters file-like object.

    Yields:
      EventFormatter: event formatters.
    """
    yaml_generator = yaml.safe_load_all(file_object)

    for yaml_definition in yaml_generator:
      yield self._ReadFormatterDefinition(yaml_definition)

  def ReadFromFile(self, path):
    """Reads the event formatters from the YAML-based formatters file.

    Args:
      path (str): path to a formatters file.

    Returns:
      list[EventFormatter]: event formatters.
    """
    with io.open(path, 'r', encoding='utf-8') as file_object:
      return list(self._ReadFromFileObject(file_object))
