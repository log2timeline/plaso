# -*- coding: utf-8 -*-
"""This file contains the interface for ESE database plugins."""

import logging

import construct
import pyesedb  # pylint: disable=wrong-import-order

from plaso.parsers import plugins


class ESEDBPlugin(plugins.BasePlugin):
  """The ESE database plugin interface."""

  NAME = u'esedb'

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

  _UINT64_BIG_ENDIAN = construct.UBInt64(u'value')
  _UINT64_LITTLE_ENDIAN = construct.ULInt64(u'value')

  # Dictionary containing a callback method per table name.
  # E.g. 'SystemIndex_0A': 'ParseSystemIndex_0A'
  REQUIRED_TABLES = {}
  OPTIONAL_TABLES = {}

  def __init__(self):
    """Initializes the ESE database plugin."""
    super(ESEDBPlugin, self).__init__()
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
      return value.decode(u'ascii')

  def _ConvertValueBinaryDataToStringBase16(self, value):
    """Converts a binary data value into a base-16 (hexadecimal) string.

    Args:
      value (bytes): binary data value or None.

    Returns:
      str: string representation of binary data value or None.
    """
    if value:
      return value.encode(u'hex')

  def _ConvertValueBinaryDataToUBInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value (bytes): binary data value containing an unsigned 64-bit big-endian
          integer.

    Returns:
      int: integer representation of binary data value or None.
    """
    if value:
      return self._UINT64_BIG_ENDIAN.parse(value)

  def _ConvertValueBinaryDataToULInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value (int): binary data value containing an unsigned 64-bit little-endian
          integer.

    Returns:
      int: integer representation of binary data value or None.
    """
    if value:
      return self._UINT64_LITTLE_ENDIAN.parse(value)

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
      raise ValueError(u'Multi value support not implemented yet.')

    if column_type == pyesedb.column_types.NULL:
      return

    elif column_type == pyesedb.column_types.BOOLEAN:
      # TODO: implement
      raise ValueError(u'Boolean value support not implemented yet.')

    elif column_type in self.INTEGER_COLUMN_TYPES:
      if long_value:
        raise ValueError(u'Long integer value not supported.')
      return record.get_value_data_as_integer(value_entry)

    elif column_type in self.FLOATING_POINT_COLUMN_TYPES:
      if long_value:
        raise ValueError(u'Long floating point value not supported.')
      return record.get_value_data_as_floating_point(value_entry)

    elif column_type in self.STRING_COLUMN_TYPES:
      if long_value:
        return long_value.get_data_as_string()
      return record.get_value_data_as_string(value_entry)

    elif column_type == pyesedb.column_types.GUID:
      # TODO: implement
      raise ValueError(u'GUID value support not implemented yet.')

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
        logging.warning(
            u'[{0:s}] duplicate column: {1:s} in table: {2:s}'.format(
                self.NAME, column_name, table_name))
        continue

      value_callback = None
      if value_mappings and column_name in value_mappings:
        value_callback_method = value_mappings.get(column_name)
        if value_callback_method:
          value_callback = getattr(self, value_callback_method, None)
          if value_callback is None:
            logging.warning((
                u'[{0:s}] missing value callback method: {1:s} for column: '
                u'{2:s} in table: {3:s}').format(
                    self.NAME, value_callback_method, column_name, table_name))

      try:
        value = self._GetRecordValue(record, value_entry)
      except ValueError as exception:
        logging.warning(exception)

      if value_callback:
        value = value_callback(value)

      record_values[column_name] = value

    return record_values

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
      raise ValueError(u'Invalid database.')

    for table_name, callback_method in iter(self._tables.items()):
      if parser_mediator.abort:
        break

      if not callback_method:
        # Table names without a callback method are allowed to improve
        # the detection of a database based on its table names.
        continue

      callback = getattr(self, callback_method, None)
      if callback is None:
        logging.warning(
            u'[{0:s}] missing callback method: {1:s} for table: {2:s}'.format(
                self.NAME, callback_method, table_name))
        continue

      esedb_table = database.get_table_by_name(table_name)
      if not esedb_table:
        logging.warning(u'[{0:s}] missing table: {1:s}'.format(
            self.NAME, table_name))
        continue

      # The database is passed in case the database contains table names
      # that are assigned dynamically and cannot be defined by
      # the table name-callback mechanism.
      callback(
          parser_mediator, cache=cache, database=database, table=esedb_table,
          **kwargs)

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
      raise ValueError(u'Invalid database.')

    # This will raise if unhandled keyword arguments are passed.
    super(ESEDBPlugin, self).Process(parser_mediator)

    self.GetEntries(
        parser_mediator, cache=cache, database=database, **kwargs)
