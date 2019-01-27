# -*- coding: utf-8 -*-
"""Windows Event Log resources database reader."""

from __future__ import unicode_literals

import re

try:
  from pysqlite2 import dbapi2 as sqlite3  # pylint: disable=wrong-import-order
except ImportError:
  import sqlite3  # pylint: disable=wrong-import-order


# TODO: Move the generic sqlite3 code to a different spot e.g. lib/.
class Sqlite3DatabaseFile(object):
  """Class that defines a sqlite3 database file."""

  _HAS_TABLE_QUERY = (
      'SELECT name FROM sqlite_master '
      'WHERE type = "table" AND name = "{0:s}"')

  def __init__(self):
    """Initializes the database file object."""
    super(Sqlite3DatabaseFile, self).__init__()
    self._connection = None
    self._cursor = None
    self.filename = None
    self.read_only = None

  def Close(self):
    """Closes the database file.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError('Cannot close database not opened.')

    # We need to run commit or not all data is stored in the database.
    self._connection.commit()
    self._connection.close()

    self._connection = None
    self._cursor = None
    self.filename = None
    self.read_only = None

  def HasTable(self, table_name):
    """Determines if a specific table exists.

    Args:
      table_name (str): table name.

    Returns:
      bool: True if the table exists.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(
          'Cannot determine if table exists database not opened.')

    sql_query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(sql_query)
    if self._cursor.fetchone():
      return True

    return False

  def GetValues(self, table_names, column_names, condition):
    """Retrieves values from a table.

    Args:
      table_names (list[str]): table names.
      column_names (list[str]): column names.
      condition (str): query condition such as
          "log_source == 'Application Error'".

    Yields:
      sqlite3.row: row.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError('Cannot retrieve values database not opened.')

    if condition:
      condition = ' WHERE {0:s}'.format(condition)

    sql_query = 'SELECT {1:s} FROM {0:s}{2:s}'.format(
        ', '.join(table_names), ', '.join(column_names), condition)

    self._cursor.execute(sql_query)

    # TODO: have a look at https://docs.python.org/2/library/
    # sqlite3.html#sqlite3.Row.
    for row in self._cursor:
      yield {
          column_name: row[column_index]
          for column_index, column_name in enumerate(column_names)}

  def Open(self, filename, read_only=False):
    """Opens the database file.

    Args:
      filename (str): filename of the database.
      read_only (Optional[bool]): True if the database should be opened in
          read-only mode. Since sqlite3 does not support a real read-only
          mode we fake it by only permitting SELECT queries.

    Returns:
      bool: True if successful.

    Raises:
      RuntimeError: if the database is already opened.
    """
    if self._connection:
      raise RuntimeError('Cannot open database already opened.')

    self.filename = filename
    self.read_only = read_only

    try:
      self._connection = sqlite3.connect(filename)
    except sqlite3.OperationalError:
      return False

    if not self._connection:
      return False

    self._cursor = self._connection.cursor()
    if not self._cursor:
      return False

    return True


class Sqlite3DatabaseReader(object):
  """Class to represent a sqlite3 database reader."""

  def __init__(self):
    """Initializes the database reader object."""
    super(Sqlite3DatabaseReader, self).__init__()
    self._database_file = Sqlite3DatabaseFile()

  def Close(self):
    """Closes the database reader object."""
    self._database_file.Close()

  def Open(self, filename):
    """Opens the database reader object.

    Args:
      filename (str): filename of the database.

    Returns:
      bool: True if successful.
    """
    return self._database_file.Open(filename, read_only=True)


class WinevtResourcesSqlite3DatabaseReader(Sqlite3DatabaseReader):
  """Class to represent a sqlite3 Event Log resources database reader."""

  # Message string specifiers that are considered white space.
  _WHITE_SPACE_SPECIFIER_RE = re.compile(r'(%[0b]|[\r\n])')
  # Message string specifiers that expand to text.
  _TEXT_SPECIFIER_RE = re.compile(r'%([ .!%nrt])')
  # Curly brackets in a message string.
  _CURLY_BRACKETS = re.compile(r'([\{\}])')
  # Message string specifiers that expand to a variable place holder.
  _PLACE_HOLDER_SPECIFIER_RE = re.compile(r'%([1-9][0-9]?)[!]?[s]?[!]?')

  def __init__(self):
    """Initializes the database reader object."""
    super(WinevtResourcesSqlite3DatabaseReader, self).__init__()
    self._string_format = 'wrc'

  def _GetEventLogProviderKey(self, log_source):
    """Retrieves the Event Log provider key.

    Args:
      log_source (str): Event Log source.

    Returns:
      str: Event Log provider key or None if not available.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = ['event_log_providers']
    column_names = ['event_log_provider_key']
    condition = 'log_source == "{0:s}"'.format(log_source)

    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return None

    if number_of_values == 1:
      values = values_list[0]
      return values['event_log_provider_key']

    raise RuntimeError('More than one value found in database.')

  def _GetMessage(self, message_file_key, lcid, message_identifier):
    """Retrieves a specific message from a specific message table.

    Args:
      message_file_key (int): message file key.
      lcid (int): language code identifier (LCID).
      message_identifier (int): message identifier.

    Returns:
      str: message string or None if not available.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_name = 'message_table_{0:d}_0x{1:08x}'.format(message_file_key, lcid)

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      return None

    column_names = ['message_string']
    condition = 'message_identifier == "0x{0:08x}"'.format(message_identifier)

    values = list(self._database_file.GetValues(
        [table_name], column_names, condition))

    number_of_values = len(values)
    if number_of_values == 0:
      return None

    if number_of_values == 1:
      return values[0]['message_string']

    raise RuntimeError('More than one value found in database.')

  def _GetMessageFileKeys(self, event_log_provider_key):
    """Retrieves the message file keys.

    Args:
      event_log_provider_key (int): Event Log provider key.

    Yields:
      int: message file key.
    """
    table_names = ['message_file_per_event_log_provider']
    column_names = ['message_file_key']
    condition = 'event_log_provider_key == {0:d}'.format(
        event_log_provider_key)

    generator = self._database_file.GetValues(
        table_names, column_names, condition)
    for values in generator:
      yield values['message_file_key']

  def _ReformatMessageString(self, message_string):
    """Reformats the message string.

    Args:
      message_string (str): message string.

    Returns:
      str: message string in Python format() (PEP 3101) style.
    """
    def _PlaceHolderSpecifierReplacer(match_object):
      """Replaces message string place holders into Python format() style."""
      expanded_groups = []
      for group in match_object.groups():
        try:
          place_holder_number = int(group, 10) - 1
          expanded_group = '{{{0:d}:s}}'.format(place_holder_number)
        except ValueError:
          expanded_group = group

        expanded_groups.append(expanded_group)

      return ''.join(expanded_groups)

    if not message_string:
      return None

    message_string = self._WHITE_SPACE_SPECIFIER_RE.sub(r'', message_string)
    message_string = self._TEXT_SPECIFIER_RE.sub(r'\\\1', message_string)
    message_string = self._CURLY_BRACKETS.sub(r'\1\1', message_string)
    return self._PLACE_HOLDER_SPECIFIER_RE.sub(
        _PlaceHolderSpecifierReplacer, message_string)

  def GetMessage(self, log_source, lcid, message_identifier):
    """Retrieves a specific message for a specific Event Log source.

    Args:
      log_source (str): Event Log source.
      lcid (int): language code identifier (LCID).
      message_identifier (int): message identifier.

    Returns:
      str: message string or None if not available.
    """
    event_log_provider_key = self._GetEventLogProviderKey(log_source)
    if not event_log_provider_key:
      return None

    generator = self._GetMessageFileKeys(event_log_provider_key)
    if not generator:
      return None

    # TODO: cache a number of message strings.
    message_string = None
    for message_file_key in generator:
      message_string = self._GetMessage(
          message_file_key, lcid, message_identifier)

      if message_string:
        break

    if self._string_format == 'wrc':
      message_string = self._ReformatMessageString(message_string)

    return message_string

  def GetMetadataAttribute(self, attribute_name):
    """Retrieves the metadata attribute.

    Args:
      attribute_name (str): name of the metadata attribute.

    Returns:
      str: the metadata attribute or None.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_name = 'metadata'

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      return None

    column_names = ['value']
    condition = 'name == "{0:s}"'.format(attribute_name)

    values = list(self._database_file.GetValues(
        [table_name], column_names, condition))

    number_of_values = len(values)
    if number_of_values == 0:
      return None

    if number_of_values == 1:
      return values[0]['value']

    raise RuntimeError('More than one value found in database.')

  def Open(self, filename):
    """Opens the database reader object.

    Args:
      filename (str): filename of the database.

    Returns:
      bool: True if successful.

    Raises:
      RuntimeError: if the version or string format of the database
                    is not supported.
    """
    if not super(WinevtResourcesSqlite3DatabaseReader, self).Open(filename):
      return False

    version = self.GetMetadataAttribute('version')
    if not version or version != '20150315':
      raise RuntimeError('Unsupported version: {0:s}'.format(version))

    string_format = self.GetMetadataAttribute('string_format')
    if not string_format:
      string_format = 'wrc'

    if string_format not in ('pep3101', 'wrc'):
      raise RuntimeError('Unsupported string format: {0:s}'.format(
          string_format))

    self._string_format = string_format
    return True
