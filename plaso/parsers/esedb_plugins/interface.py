# -*- coding: utf-8 -*-
"""This file contains the interface for ESE database plugins."""

import os
import uuid

import pyesedb

from dfdatetime import filetime as dfdatetime_filetime

from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins


class ESEDBPlugin(plugins.BasePlugin, dtfabric_helper.DtFabricHelper):
  """The ESE database plugin interface."""

  NAME = 'esedb_plugin'
  DATA_FORMAT = 'ESE database file'

  BINARY_DATA_COLUMN_TYPES = frozenset([
      pyesedb.column_types.BINARY_DATA,
      pyesedb.column_types.LARGE_BINARY_DATA])

  FLOATING_POINT_COLUMN_TYPES = frozenset([
      pyesedb.column_types.FLOAT_32BIT,
      pyesedb.column_types.DOUBLE_64BIT])

  INTEGER_COLUMN_TYPES = frozenset([
      pyesedb.column_types.CURRENCY,
      pyesedb.column_types.DATE_TIME,
      pyesedb.column_types.INTEGER_8BIT_UNSIGNED,
      pyesedb.column_types.INTEGER_16BIT_SIGNED,
      pyesedb.column_types.INTEGER_16BIT_UNSIGNED,
      pyesedb.column_types.INTEGER_32BIT_SIGNED,
      pyesedb.column_types.INTEGER_32BIT_UNSIGNED,
      pyesedb.column_types.INTEGER_64BIT_SIGNED])

  STRING_COLUMN_TYPES = frozenset([
      pyesedb.column_types.TEXT,
      pyesedb.column_types.LARGE_TEXT])

  # Dictionary containing a callback method per table name.
  # E.g. 'SystemIndex_0A': 'ParseSystemIndex_0A'
  REQUIRED_TABLES = {}
  OPTIONAL_TABLES = {}

  # The dtFabric definition file.
  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'types.yaml')

  def __init__(self):
    """Initializes the ESE database plugin."""
    super(ESEDBPlugin, self).__init__()
    self._tables = {}
    self._tables.update(self.REQUIRED_TABLES)
    self._tables.update(self.OPTIONAL_TABLES)

  def _ConvertValueBinaryDataToStringAscii(self, value):
    """Converts a binary data value into a string.

    Args:
      value (bytes): binary data value containing an ASCII string or None.

    Returns:
      str: string representation of binary data value or None.
    """
    if value:
      return value.decode('ascii')

    return None

  def _ConvertValueBinaryDataToStringBase16(self, value):
    """Converts a binary data value into a base-16 (hexadecimal) string.

    Args:
      value (bytes): binary data value or None.

    Returns:
      str: string representation of binary data value or None.
    """
    if value:
      return value.encode('hex')

    return None

  def _ConvertValueBinaryDataToUBInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value (bytes): binary data value containing an unsigned 64-bit big-endian
          integer.

    Returns:
      int: integer representation of binary data value or None if value is
          not set.

    Raises:
      ParseError: if the integer value cannot be parsed.
    """
    if not value:
      return None

    integer_map = self._GetDataTypeMap('uint64be')

    try:
      return self._ReadStructureFromByteStream(value, 0, integer_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse integer value with error: {0!s}'.format(
              exception))

  def _ConvertValueBinaryDataToULInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value (int): binary data value containing an unsigned 64-bit little-endian
          integer.

    Returns:
      int: integer representation of binary data value or None if value is
          not set.

    Raises:
      ParseError: if the integer value cannot be parsed.
    """
    if not value:
      return None

    integer_map = self._GetDataTypeMap('uint64le')

    try:
      return self._ReadStructureFromByteStream(value, 0, integer_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.ParseError(
          'Unable to parse integer value with error: {0!s}'.format(
              exception))

  def _GetFiletimeRecordValue(self, record_values, value_name):
    """Retrieves a FILETIME record value.

    Args:
      record_values (dict[str,object]): values per column name.
      value_name (str): name of the record value.

    Returns:
      dfdatetime.Filetime: date and time or None if not set.
    """
    filetime = record_values.get(value_name, None)
    if not filetime:
      return None

    return dfdatetime_filetime.Filetime(timestamp=filetime)

  def _GetRecordValue(self, record, value_entry):
    """Retrieves a specific value from the record.

    Args:
      record (pyesedb.record): ESE record.
      value_entry (int): value entry.

    Returns:
      object: value or None if not available.

    Raises:
      ValueError: if the value is not supported.
    """
    column_type = record.get_column_type(value_entry)
    long_value = None

    if record.is_long_value(value_entry):
      long_value = record.get_value_data_as_long_value(value_entry)

    if record.is_multi_value(value_entry):
      # TODO: implement
      raise ValueError('Multi value support not implemented yet.')

    if column_type == pyesedb.column_types.NULL:
      return None

    if column_type == pyesedb.column_types.BOOLEAN:
      if long_value:
        # TODO: implement
        raise ValueError('Long boolean value not supported.')
      return record.get_value_data_as_boolean(value_entry)

    if column_type in self.INTEGER_COLUMN_TYPES:
      if long_value:
        raise ValueError('Long integer value not supported.')
      return record.get_value_data_as_integer(value_entry)

    if column_type == pyesedb.column_types.GUID:
      if long_value:
        # TODO: implement
        raise ValueError('Long GUID value not supported.')
      value_data = record.get_value_data(value_entry)
      if value_data:
        value_data = uuid.UUID(bytes_le=value_data)
      return value_data

    if column_type in self.FLOATING_POINT_COLUMN_TYPES:
      if long_value:
        raise ValueError('Long floating point value not supported.')
      return record.get_value_data_as_floating_point(value_entry)

    if column_type in self.STRING_COLUMN_TYPES:
      if long_value:
        return long_value.get_data_as_string()
      return record.get_value_data_as_string(value_entry)

    if long_value:
      return long_value.get_data()
    return record.get_value_data(value_entry)

  def _GetRecordValues(
      self, parser_mediator, table_name, record_index, record,
      value_mappings=None):
    """Retrieves the values from the record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      table_name (str): name of the table.
      record_index (int): ESE record index.
      record (pyesedb.record): ESE record.
      value_mappings (Optional[dict[str, str]]): value mappings, which map
          the column name to a callback method.

    Returns:
      dict[str,object]: values per column name.
    """
    record_values = {}

    for value_entry in range(0, record.number_of_values):
      if parser_mediator.abort:
        break

      column_name = record.get_column_name(value_entry)
      if column_name in record_values:
        parser_mediator.ProduceExtractionWarning(
            '[{0:s}] duplicate column: {1:s} in table: {2:s}'.format(
                self.NAME, column_name, table_name))
        continue

      value_callback = None
      if value_mappings and column_name in value_mappings:
        value_callback_method = value_mappings.get(column_name)
        if value_callback_method:
          value_callback = getattr(self, value_callback_method, None)
          if value_callback is None:
            logger.warning((
                '[{0:s}] missing value callback method: {1:s} for column: '
                '{2:s} in table: {3:s}').format(
                    self.NAME, value_callback_method, column_name, table_name))

      if value_callback:
        try:
          value_data = record.get_value_data(value_entry)
          value = value_callback(value_data)

        except Exception as exception:  # pylint: disable=broad-except
          logger.error(exception)
          value = None
          parser_mediator.ProduceExtractionWarning((
              'unable to parse value: {0:s} in record: {1:d} with callback: '
              '{2:s} in table: {3:s} with error: {4!s}').format(
                  column_name, record_index, value_callback_method, table_name,
                  exception))

      else:
        try:
          value = self._GetRecordValue(record, value_entry)
        except ValueError as exception:
          value = None
          parser_mediator.ProduceExtractionWarning((
              'unable to parse value: {0:s}  in record: {1:d} in table: {2:s} '
              'with error: {3!s}').format(
                  column_name, record_index, table_name, exception))

      record_values[column_name] = value

    return record_values

  def _ParseESEDatabase(
      self, parser_mediator, cache=None, database=None, **kwargs):
    """Extracts event objects from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[ESEDatabase]): ESE database.

    Raises:
      ValueError: If the database attribute is not valid.
    """
    if database is None:
      raise ValueError('Invalid database.')

    for table_name, callback_method in sorted(self._tables.items()):
      if parser_mediator.abort:
        break

      if not callback_method:
        # Table names without a callback method are allowed to improve
        # the detection of a database based on its table names.
        continue

      callback = getattr(self, callback_method, None)
      if callback is None:
        logger.warning(
            '[{0:s}] missing callback method: {1:s} for table: {2:s}'.format(
                self.NAME, callback_method, table_name))
        continue

      esedb_table = database.GetTableByName(table_name)
      if not esedb_table:
        if table_name not in self.OPTIONAL_TABLES:
          logger.warning('[{0:s}] missing table: {1:s}'.format(
              self.NAME, table_name))
        continue

      # The database is passed in case the database contains table names
      # that are assigned dynamically and cannot be defined by
      # the table name-callback mechanism.
      callback(
          parser_mediator, cache=cache, database=database, table=esedb_table,
          **kwargs)

  def CheckRequiredTables(self, database):
    """Check if the database has the minimal structure required by the plugin.

    Args:
      database (ESEDatabase): ESE database to check.

    Returns:
      bool: True if the database has the minimum tables defined by the plugin,
          or False if it does not or no required tables are defined. The
          database can have more tables than specified by the plugin and still
          return True.
    """
    if not self.REQUIRED_TABLES:
      return False

    return set(self.REQUIRED_TABLES.keys()).issubset(database.tables)

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, cache=None, database=None, **kwargs):
    """Extracts events from an ESE database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[ESEDatabase]): ESE database.

    Raises:
      ValueError: If the database argument is not valid.
    """
    if database is None:
      raise ValueError('Invalid database.')

    # This will raise if unhandled keyword arguments are passed.
    super(ESEDBPlugin, self).Process(parser_mediator)

    self._ParseESEDatabase(
        parser_mediator, cache=cache, database=database, **kwargs)
