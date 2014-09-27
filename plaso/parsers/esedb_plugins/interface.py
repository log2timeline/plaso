#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the interface for ESE database plugins."""

import construct
import logging

import pyesedb

from plaso.lib import errors
from plaso.parsers import plugins


class EseDbPlugin(plugins.BasePlugin):
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

  _UINT64_BIG_ENDIAN = construct.UBInt64('value')
  _UINT64_LITTLE_ENDIAN = construct.ULInt64('value')

  # Dictionary containing a callback method per table name.
  # E.g. 'SystemIndex_0A': 'ParseSystemIndex_0A'
  REQUIRED_TABLES = {}
  OPTIONAL_TABLES = {}

  def __init__(self):
    """Initializes the ESE database plugin."""
    super(EseDbPlugin, self).__init__()
    self._required_tables = frozenset(self.REQUIRED_TABLES.keys())
    self._tables = {}
    self._tables.update(self.REQUIRED_TABLES)
    self._tables.update(self.OPTIONAL_TABLES)

  def _ConvertValueBinaryDataToStringAscii(self, value):
    """Converts a binary data value into a string.

    Args:
      value: The binary data value containing an ASCII string or None.

    Returns:
      A string or None if value is None.
    """
    if value:
      return value.decode('ascii')

  def _ConvertValueBinaryDataToStringBase16(self, value):
    """Converts a binary data value into a base-16 (hexadecimal) string.

    Args:
      value: The binary data value or None.

    Returns:
      A string or None if value is None.
    """
    if value:
      return value.encode('hex')

  def _ConvertValueBinaryDataToUBInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value: The binary data value containing an unsigned 64-bit big-endian
             integer.

    Returns:
      An integer or None if value is None.
    """
    if value:
      return self._UINT64_BIG_ENDIAN.parse(value)

  def _ConvertValueBinaryDataToULInt64(self, value):
    """Converts a binary data value into an integer.

    Args:
      value: The binary data value containing an unsigned 64-bit little-endian
             integer.

    Returns:
      An integer or None if value is None.
    """
    if value:
      return self._UINT64_LITTLE_ENDIAN.parse(value)

  def _GetRecordValue(self, record, value_entry):
    """Retrieves a specific value from the record.

    Args:
      record: The ESE record object (instance of pyesedb.record).
      value_entry: The value entry.

    Returns:
      An object containing the value.
    """
    column_type = record.get_column_type(value_entry)
    value_data_flags = record.get_value_data_flags(value_entry)

    if value_data_flags & pyesedb.value_flags.MULTI_VALUE:
      # TODO: implement
      pass

    elif column_type == pyesedb.column_types.NULL:
      return

    elif column_type == pyesedb.column_types.BOOLEAN:
      # TODO: implement
      pass

    elif column_type in self.INTEGER_COLUMN_TYPES:
      return record.get_value_data_as_integer(value_entry)

    elif column_type in self.FLOATING_POINT_COLUMN_TYPES:
      return record.get_value_data_as_floating_point(value_entry)

    elif column_type in self.STRING_COLUMN_TYPES:
      return record.get_value_data_as_string(value_entry)

    elif column_type == pyesedb.column_types.GUID:
      # TODO: implement
      pass

    return record.get_value_data(value_entry)

  def _GetRecordValues(self, table_name, record, value_mappings=None):
    """Retrieves the values from the record.

    Args:
      table_name: The name of the table.
      record: The ESE record object (instance of pyesedb.record).
      value_mappings: Optional dict of value mappings, which map the column
                      name to a callback method. The default is None.

    Returns:
      An dict containing the values.
    """
    record_values = {}

    for value_entry in range(0, record.number_of_values):
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

      value = self._GetRecordValue(record, value_entry)
      if value_callback:
        value = value_callback(value)

      record_values[column_name] = value

    return record_values

  def _GetTableNames(self, database):
    """Retrieves the table names in a database.

    Args:
      database: The ESE database object (instance of pyesedb.file).

    Returns:
      A list of the table names.
    """
    table_names = []
    for esedb_table in database.tables:
      table_names.append(esedb_table.name)

    return table_names

  def GetEntries(self, parser_context, database=None, cache=None, **kwargs):
    """Extracts event objects from the database.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      database: Optional ESE database object (instance of pyesedb.file).
                The default is None.
      cache: Optional cache object (instance of EseDbCache). The default is
             None.

    Raises:
      ValueError: If the database attribute is not valid.
    """
    if database is None:
      raise ValueError(u'Invalid database.')

    for table_name, callback_method in self._tables.iteritems():
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
          parser_context, database=database, table=esedb_table, cache=cache,
          **kwargs)

  def Process(self, parser_context, database=None, cache=None, **kwargs):
    """Determines if this is the appropriate plugin for the database.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      database: Optional ESE database object (instance of pyesedb.file).
                The default is None.
      cache: Optional cache object (instance of EseDbCache). The default is
             None.

    Raises:
      errors.WrongPlugin: If the database does not contain all the tables
                          defined in the required_tables set.
      ValueError: If the database attribute is not valid.
    """
    if database is None:
      raise ValueError(u'Invalid database.')

    table_names = frozenset(self._GetTableNames(database))
    if self._required_tables.difference(table_names):
      raise errors.WrongPlugin(
          u'[{0:s}] required tables not found.'.format(self.NAME))

    # This will raise if unhandled keyword arguments are passed.
    super(EseDbPlugin, self).Process(parser_context, **kwargs)

    self.GetEntries(
        parser_context, database=database, cache=cache, **kwargs)
