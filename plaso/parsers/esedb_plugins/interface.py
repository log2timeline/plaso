# -*- coding: utf-8 -*-
"""This file contains the interface for ESE database plugins."""

from __future__ import unicode_literals

import os

import pyesedb

from dtfabric import errors as dtfabric_errors
from dtfabric.runtime import fabric as dtfabric_fabric

from plaso.lib import errors
from plaso.parsers import logger
from plaso.parsers import plugins


class ESEDBPlugin(plugins.BasePlugin):
  """The ESE database plugin interface."""

  NAME = 'esedb'

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
  _DEFINITION_FILE = 'types.yaml'

  # Preserve the absolute path value of __file__ in case it is changed
  # at run-time.
  _DEFINITION_FILES_PATH = os.path.dirname(__file__)

  def __init__(self):
    """Initializes the ESE database plugin."""
    super(ESEDBPlugin, self).__init__()
    self._data_type_maps = {}
    self._fabric = self._ReadDefinitionFile(self._DEFINITION_FILE)
    self._tables = {}
    self._tables.update(self.REQUIRED_TABLES)
    self._tables.update(self.OPTIONAL_TABLES)

  @property
  def required_tables(self):
    """set[str]: required table names."""
    return frozenset(self.REQUIRED_TABLES.keys())

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

  def _GetDataTypeMap(self, name):
    """Retrieves a data type map defined by the definition file.

    The data type maps are cached for reuse.

    Args:
      name (str): name of the data type as defined by the definition file.

    Returns:
      dtfabric.DataTypeMap: data type map which contains a data type definition,
          such as a structure, that can be mapped onto binary data.
    """
    data_type_map = self._data_type_maps.get(name, None)
    if not data_type_map:
      data_type_map = self._fabric.CreateDataTypeMap(name)
      self._data_type_maps[name] = data_type_map

    return data_type_map

  def _GetRecordValue(self, record, value_entry):
    """Retrieves a specific value from the record.

    Args:
      record (pyesedb.record): ESE record.
      value_entry (int): value entry.

    Returns:
      object: value.

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
      # TODO: implement
      raise ValueError('Boolean value support not implemented yet.')

    if column_type in self.INTEGER_COLUMN_TYPES:
      if long_value:
        raise ValueError('Long integer value not supported.')
      return record.get_value_data_as_integer(value_entry)

    if column_type in self.FLOATING_POINT_COLUMN_TYPES:
      if long_value:
        raise ValueError('Long floating point value not supported.')
      return record.get_value_data_as_floating_point(value_entry)

    if column_type in self.STRING_COLUMN_TYPES:
      if long_value:
        return long_value.get_data_as_string()
      return record.get_value_data_as_string(value_entry)

    if column_type == pyesedb.column_types.GUID:
      # TODO: implement
      raise ValueError('GUID value support not implemented yet.')

    if long_value:
      return long_value.get_data()
    return record.get_value_data(value_entry)

  def _GetRecordValues(
      self, parser_mediator, table_name, record, value_mappings=None):
    """Retrieves the values from the record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      table_name (str): name of the table.
      record (pyesedb.record): ESE record.
      value_mappings (Optional[dict[str, str]): value mappings, which map
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
        logger.warning(
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
              'unable to parse value: {0:s} with callback: {1:s} with error: '
              '{2!s}').format(column_name, value_callback_method, exception))

      else:
        try:
          value = self._GetRecordValue(record, value_entry)
        except ValueError as exception:
          value = None
          parser_mediator.ProduceExtractionWarning(
              'unable to parse value: {0:s} with error: {1!s}'.format(
                  column_name, exception))

      record_values[column_name] = value

    return record_values

  def _ReadDefinitionFile(self, filename):
    """Reads a dtFabric definition file.

    Args:
      filename (str): name of the dtFabric definition file.

    Returns:
      dtfabric.DataTypeFabric: data type fabric which contains the data format
          data type maps of the data type definition, such as a structure, that
          can be mapped onto binary data or None if no filename is provided.
    """
    if not filename:
      return None

    path = os.path.join(self._DEFINITION_FILES_PATH, filename)
    with open(path, 'rb') as file_object:
      definition = file_object.read()

    return dtfabric_fabric.DataTypeFabric(yaml_definition=definition)

  def _ReadStructureFromByteStream(
      self, byte_stream, file_offset, data_type_map, context=None):
    """Reads a structure from a byte stream.

    Args:
      byte_stream (bytes): byte stream.
      file_offset (int): offset of the structure data relative to the start
          of the file-like object.
      data_type_map (dtfabric.DataTypeMap): data type map of the structure.
      context (Optional[dtfabric.DataTypeMapContext]): data type map context.
          The context is used within dtFabric to hold state about how to map
          the data type definition onto the byte stream. In this class it is
          used to determine the size of variable size data type definitions.

    Returns:
      object: structure values object.

    Raises:
      ParseError: if the structure cannot be read.
      ValueError: if file-like object or data type map is missing.
    """
    if not byte_stream:
      raise ValueError('Missing byte stream.')

    if not data_type_map:
      raise ValueError('Missing data type map.')

    try:
      return data_type_map.MapByteStream(byte_stream, context=context)
    except (dtfabric_errors.ByteStreamTooSmallError,
            dtfabric_errors.MappingError) as exception:
      raise errors.ParseError((
          'Unable to map {0:s} data at offset: 0x{1:08x} with error: '
          '{2!s}').format(data_type_map.name or '', file_offset, exception))

  def GetEntries(self, parser_mediator, cache=None, database=None, **kwargs):
    """Extracts event objects from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[pyesedb.file]): ESE database.

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

      esedb_table = database.get_table_by_name(table_name)
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

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, cache=None, database=None, **kwargs):
    """Determines if this is the appropriate plugin for the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      cache (Optional[ESEDBCache]): cache.
      database (Optional[pyesedb.file]): ESE database.

    Raises:
      ValueError: If the database attribute is not valid.
    """
    if database is None:
      raise ValueError('Invalid database.')

    # This will raise if unhandled keyword arguments are passed.
    super(ESEDBPlugin, self).Process(parser_mediator)

    self.GetEntries(
        parser_mediator, cache=cache, database=database, **kwargs)
