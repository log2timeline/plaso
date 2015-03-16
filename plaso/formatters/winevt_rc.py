# -*- coding: utf-8 -*-
"""Windows Event Log resources database reader."""

import re

import sqlite3


# TODO: Move the generic sqlite3 code to a different spot e.g. lib/.
class Sqlite3DatabaseFile(object):
  """Class that defines a sqlite3 database file."""

  _HAS_TABLE_QUERY = (
      u'SELECT name FROM sqlite_master '
      u'WHERE type = "table" AND name = "{0:s}"')

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
      raise RuntimeError(u'Cannot close database not opened.')

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
      table_name: the table name.

    Returns:
      True if the table exists, false otheriwse.

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(
          u'Cannot determine if table exists database not opened.')

    sql_query = self._HAS_TABLE_QUERY.format(table_name)

    self._cursor.execute(sql_query)
    if self._cursor.fetchone():
      return True

    return False

  def GetValues(self, table_names, column_names, condition):
    """Retrieves values from a table.

    Args:
      table_names: list of table names.
      column_names: list of column names.
      condition: string containing the condition.

    Yields:
      A row object (instance of sqlite3.row).

    Raises:
      RuntimeError: if the database is not opened.
    """
    if not self._connection:
      raise RuntimeError(u'Cannot retrieve values database not opened.')

    if condition:
      condition = u' WHERE {0:s}'.format(condition)

    sql_query = u'SELECT {1:s} FROM {0:s}{2:s}'.format(
        u', '.join(table_names), u', '.join(column_names), condition)

    self._cursor.execute(sql_query)

    # TODO: have a look at https://docs.python.org/2/library/
    # sqlite3.html#sqlite3.Row.
    for row in self._cursor:
      values = {}
      for column_index in range(0, len(column_names)):
        column_name = column_names[column_index]
        values[column_name] = row[column_index]
      yield values

  def Open(self, filename, read_only=False):
    """Opens the database file.

    Args:
      filename: the filename of the database.
      read_only: optional boolean value to indicate the database should be
                 opened in read-only mode. The default is false. Since sqlite3
                 does not support a real read-only mode we fake it by only
                 permitting SELECT queries.

    Returns:
      A boolean containing True if successful or False if not.

    Raises:
      RuntimeError: if the database is already opened.
    """
    if self._connection:
      raise RuntimeError(u'Cannot open database already opened.')

    self.filename = filename
    self.read_only = read_only

    self._connection = sqlite3.connect(filename)
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
      filename: the filename of the database.

    Returns:
      A boolean containing True if successful or False if not.
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
    self._string_format = u'wrc'

  def _GetEventLogProviderKey(self, log_source):
    """Retrieves the Event Log provider key.

    Args:
      log_source: the Event Log source.

    Returns:
      An Event Log provider key or None if not available.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_names = [u'event_log_providers']
    column_names = [u'event_log_provider_key']
    condition = u'log_source == "{0:s}"'.format(log_source)

    values_list = list(self._database_file.GetValues(
        table_names, column_names, condition))

    number_of_values = len(values_list)
    if number_of_values == 0:
      return

    elif number_of_values == 1:
      values = values_list[0]
      return values[u'event_log_provider_key']

    raise RuntimeError(u'More than one value found in database.')

  def _GetMessage(self, message_file_key, lcid, message_identifier):
    """Retrieves a specific message from a specific message table.

    Args:
      message_file_key: the message file key.
      lcid: integer containing the language code identifier (LCID).
      message_identifier: the message identifier.

    Returns:
      The message string or None if not available.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_name = u'message_table_{0:d}_0x{1:08x}'.format(message_file_key, lcid)

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      return

    column_names = [u'message_string']
    condition = u'message_identifier == "0x{0:08x}"'.format(message_identifier)

    values = list(self._database_file.GetValues(
        [table_name], column_names, condition))

    number_of_values = len(values)
    if number_of_values == 0:
      return

    elif number_of_values == 1:
      return values[0][u'message_string']

    raise RuntimeError(u'More than one value found in database.')

  def _GetMessageFileKeys(self, event_log_provider_key):
    """Retrieves the message file keys.

    Args:
      event_log_provider_key: the Event Log provider key.

    Yields:
      A message file key.
    """
    table_names = [u'message_file_per_event_log_provider']
    column_names = [u'message_file_key']
    condition = u'event_log_provider_key == {0:d}'.format(
        event_log_provider_key)

    generator = self._database_file.GetValues(
        table_names, column_names, condition)

    if generator:
      for values in generator:
        yield values[u'message_file_key']

  def _ReformatMessageString(self, message_string):
    """Reformats the message string.

    Args:
      message_string: the message string.

    Returns:
      The message string in Python format() (PEP 3101) style.
    """
    def place_holder_specifier_replacer(match_object):
      """Replaces message string place holders into Python format() style."""
      expanded_groups = []
      for group in match_object.groups():
        try:
          place_holder_number = int(group, 10) - 1
          expanded_group = u'{{{0:d}:s}}'.format(place_holder_number)
        except ValueError:
          expanded_group = group

        expanded_groups.append(expanded_group)

      return u''.join(expanded_groups)

    if not message_string:
      return

    message_string = self._WHITE_SPACE_SPECIFIER_RE.sub(r'', message_string)
    message_string = self._TEXT_SPECIFIER_RE.sub(r'\\\1', message_string)
    message_string = self._CURLY_BRACKETS.sub(r'\1\1', message_string)
    return self._PLACE_HOLDER_SPECIFIER_RE.sub(
        place_holder_specifier_replacer, message_string)

  def GetMessage(self, log_source, lcid, message_identifier):
    """Retrieves a specific message for a specific Event Log source.

    Args:
      log_source: the Event Log source.
      lcid: the language code identifier (LCID).
      message_identifier: the message identifier.

    Returns:
      The message string or None if not available.
    """
    event_log_provider_key = self._GetEventLogProviderKey(log_source)
    if not event_log_provider_key:
      return

    generator = self._GetMessageFileKeys(event_log_provider_key)
    if not generator:
      return

    # TODO: cache a number of message strings.
    message_string = None
    for message_file_key in generator:
      message_string = self._GetMessage(
          message_file_key, lcid, message_identifier)

      if message_string:
        break

    if self._string_format == u'wrc':
      message_string = self._ReformatMessageString(message_string)

    return message_string

  def GetMetadataAttribute(self, attribute_name):
    """Retrieves the metadata attribute.

    Args:
      attribute_name: the name of the metadata attribute.

    Returns:
      The value of the metadata attribute or None.

    Raises:
      RuntimeError: if more than one value is found in the database.
    """
    table_name = u'metadata'

    has_table = self._database_file.HasTable(table_name)
    if not has_table:
      return
  
    column_names = [u'value']
    condition = u'name == "{0:s}"'.format(attribute_name)
  
    values = list(self._database_file.GetValues(
        [table_name], column_names, condition))
  
    number_of_values = len(values)
    if number_of_values == 0:
      return

    elif number_of_values == 1:
      return values[0][u'value']

    raise RuntimeError(u'More than one value found in database.')

  def Open(self, filename):
    """Opens the database reader object.

    Args:
      filename: the filename of the database.

    Returns:
      A boolean containing True if successful or False if not.

    Raises:
      RuntimeError: if the version or string format of the database
                    is not supported.
    """
    if not super(WinevtResourcesSqlite3DatabaseReader, self).Open(filename):
      return False

    version = self.GetMetadataAttribute(u'version')
    if not version or version not in [u'20150315']:
      raise RuntimeError(u'Unsupported version: {0:s}'.format(version))

    string_format = self.GetMetadataAttribute(u'string_format')
    if not string_format:
      string_format = u'wrc'

    if string_format not in [u'pep3101', u'wrc']:
      raise RuntimeError(u'Unsupported string format: {0:s}'.format(
          string_format))

    self._string_format = string_format
    return True
