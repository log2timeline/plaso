# -*- coding: utf-8 -*-
"""Windows EventLog resources database reader."""

import collections
import os
import sqlite3

from plaso.engine import path_helper
from plaso.helpers.windows import languages
from plaso.helpers.windows import resource_files
from plaso.output import logger


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


class WinevtResourcesSqlite3DatabaseReader(object):
  """Windows EventLog resources SQLite database reader."""

  def __init__(self):
    """Initializes a Windows EventLog resources SQLite database reader."""
    super(WinevtResourcesSqlite3DatabaseReader, self).__init__()
    self._database_file = Sqlite3DatabaseFile()
    self._resouce_file_helper = resource_files.WindowsResourceFileHelper
    self._string_format = 'wrc'

  def _GetEventLogProviderKey(self, log_source):
    """Retrieves the EventLog provider key.

    Args:
      log_source (str): EventLog source.

    Returns:
      str: EventLog provider key or None if not available.

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
      event_log_provider_key (int): EventLog provider key.

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

  def Close(self):
    """Closes the database reader object."""
    self._database_file.Close()

  def GetMessage(self, log_source, lcid, message_identifier):
    """Retrieves a specific message for a specific EventLog source.

    Args:
      log_source (str): EventLog source.
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

    message_string = None
    for message_file_key in generator:
      message_string = self._GetMessage(
          message_file_key, lcid, message_identifier)

      if message_string:
        break

    if self._string_format == 'wrc':
      message_string = self._resouce_file_helper.FormatMessageStringInPEP3101(
          message_string)

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
    if not self._database_file.Open(filename, read_only=True):
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


class WinevtResourcesHelper(object):
  """Windows EventLog resources helper."""

  # LCID 0x0409 is en-US.
  DEFAULT_LCID = 0x0409

  # The maximum number of cached message strings
  _MAXIMUM_CACHED_MESSAGE_STRINGS = 32 * 1024

  _WINEVT_RC_DATABASE = 'winevt-rc.db'

  def __init__(self, storage_reader, data_location, lcid):
    """Initializes Windows EventLog resources helper.

    Args:
      storage_reader (StorageReader): storage reader.
      data_location (str): data location of the winevt-rc database.
      lcid (int): Windows Language Code Identifier (LCID).
    """
    language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(
        lcid or self.DEFAULT_LCID)

    super(WinevtResourcesHelper, self).__init__()
    self._data_location = data_location
    self._environment_variables = None
    self._language_tag = language_tag.lower()
    self._lcid = lcid or self.DEFAULT_LCID
    self._message_string_cache = collections.OrderedDict()
    self._storage_reader = storage_reader
    self._windows_eventlog_message_files = None
    self._windows_eventlog_providers = None
    self._winevt_database_reader = None

  def _CacheMessageString(
      self, provider_identifier, log_source, message_identifier,
      event_version, message_string):
    """Caches a specific message string.

    Args:
      provider_identifier (str): EventLog provider identifier.
      log_source (str): EventLog source, such as "Application Error".
      message_identifier (int): message identifier.
      event_version (int): event version or None if not set.
      message_string (str): message string.
    """
    if len(self._message_string_cache) >= self._MAXIMUM_CACHED_MESSAGE_STRINGS:
      self._message_string_cache.popitem(last=True)

    if provider_identifier:
      lookup_key = '{0:s}:0x{1:08x}'.format(
          provider_identifier, message_identifier)
      if event_version is not None:
        lookup_key = '{0:s}:{1:d}'.format(lookup_key, event_version)
      self._message_string_cache[lookup_key] = message_string
      self._message_string_cache.move_to_end(lookup_key, last=False)

    if log_source:
      lookup_key = '{0:s}:0x{1:08x}'.format(log_source, message_identifier)
      if event_version is not None:
        lookup_key = '{0:s}:{1:d}'.format(lookup_key, event_version)
      self._message_string_cache[lookup_key] = message_string
      self._message_string_cache.move_to_end(lookup_key, last=False)

  def _GetCachedMessageString(
      self, provider_identifier, log_source, message_identifier, event_version):
    """Retrieves a specific cached message string.

    Args:
      provider_identifier (str): EventLog provider identifier.
      log_source (str): EventLog source, such as "Application Error".
      message_identifier (int): message identifier.
      event_version (int): event version or None if not set.

    Returns:
      str: message string or None if not available.
    """
    lookup_key = None
    message_string = None

    if provider_identifier:
      lookup_key = '{0:s}:0x{1:08x}'.format(
          provider_identifier, message_identifier)
      if event_version is not None:
        lookup_key = '{0:s}:{1:d}'.format(lookup_key, event_version)
      message_string = self._message_string_cache.get(lookup_key, None)

    if not message_string and log_source:
      lookup_key = '{0:s}:0x{1:08x}'.format(log_source, message_identifier)
      if event_version is not None:
        lookup_key = '{0:s}:{1:d}'.format(lookup_key, event_version)
      message_string = self._message_string_cache.get(lookup_key, None)

    if message_string:
      self._message_string_cache.move_to_end(lookup_key, last=False)

    return message_string

  def _GetWinevtRcDatabaseReader(self):
    """Opens the Windows EventLog resource database reader.

    Returns:
      WinevtResourcesSqlite3DatabaseReader: Windows EventLog resource
          database reader or None.
    """
    if not self._winevt_database_reader and self._data_location:
      logger.warning((
          'Falling back to {0:s}. Please make sure the Windows EventLog '
          'message strings in the database correspond to those in the '
          'EventLog files.').format(self._WINEVT_RC_DATABASE))

      database_path = os.path.join(
          self._data_location, self._WINEVT_RC_DATABASE)
      if not os.path.isfile(database_path):
        return None

      self._winevt_database_reader = WinevtResourcesSqlite3DatabaseReader()
      if not self._winevt_database_reader.Open(database_path):
        self._winevt_database_reader = None

    return self._winevt_database_reader

  def _GetWinevtRcDatabaseMessageString(self, log_source, message_identifier):
    """Retrieves a specific Windows EventLog resource database message string.

    Args:
      log_source (str): EventLog source, such as "Application Error".
      message_identifier (int): message identifier.

    Returns:
      str: message string or None if not available.
    """
    database_reader = self._GetWinevtRcDatabaseReader()
    if not database_reader:
      return None

    if self._lcid != self.DEFAULT_LCID:
      message_string = database_reader.GetMessage(
          log_source, self._lcid, message_identifier)
      if message_string:
        return message_string

    return database_reader.GetMessage(
        log_source, self.DEFAULT_LCID, message_identifier)

  def _ReadEnvironmentVariables(self, storage_reader):
    """Reads the environment variables.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    # TODO: get environment variables related to the source.
    self._environment_variables = list(storage_reader.GetAttributeContainers(
        'environment_variable'))

  def _ReadWindowsEventLogMessageFiles(self, storage_reader):
    """Reads the Windows EventLog message files.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    # TODO: get windows eventlog message files related to the source.
    self._windows_eventlog_message_files = {}
    if storage_reader.HasAttributeContainers('windows_eventlog_message_file'):
      for message_file in storage_reader.GetAttributeContainers(
          'windows_eventlog_message_file'):
        path, filename = path_helper.PathHelper.GetWindowsSystemPath(
            message_file.path, self._environment_variables)

        lookup_path = '\\'.join([path, filename]).lower()
        message_file_identifier = message_file.GetIdentifier()
        self._windows_eventlog_message_files[lookup_path] = (
            message_file_identifier)

  def _ReadWindowsEventLogMessageString(
      self, storage_reader, provider_identifier, log_source,
      message_identifier, event_version):
    """Reads an Windows EventLog message string.

    Args:
      storage_reader (StorageReader): storage reader.
      provider_identifier (str): EventLog provider identifier.
      log_source (str): EventLog source, such as "Application Error".
      message_identifier (int): message identifier.
      event_version (int): event version or None if not set.

    Returns:
      str: message string or None if not available.
    """
    if self._environment_variables is None:
      self._ReadEnvironmentVariables(storage_reader)

    if self._windows_eventlog_providers is None:
      self._ReadWindowsEventLogProviders(storage_reader)

    if self._windows_eventlog_message_files is None:
      self._ReadWindowsEventLogMessageFiles(storage_reader)

    provider = None

    if provider_identifier:
      lookup_key = provider_identifier.lower()
      provider = self._windows_eventlog_providers.get(lookup_key, None)

    if not provider:
      lookup_key = log_source.lower()
      provider = self._windows_eventlog_providers.get(lookup_key, None)

    provider = self._windows_eventlog_providers.get(lookup_key, None)
    if not provider:
      return None

    if not storage_reader.HasAttributeContainers(
        'windows_eventlog_message_string'):
      return None

    # Map the event identifier to a message identifier as defined by the
    # WEVT_TEMPLATE event definition.
    if provider_identifier and storage_reader.HasAttributeContainers(
        'windows_wevt_template_event'):
      # TODO: add message_file_identifiers to filter_expression
      filter_expression = (
          'provider_identifier == "{0:s}" and identifier == {1:d}').format(
              provider_identifier, message_identifier)
      if event_version is not None:
        filter_expression = '{0:s} and version == {1:d}'.format(
            filter_expression, event_version)

      for event_definition in storage_reader.GetAttributeContainers(
          'windows_wevt_template_event', filter_expression=filter_expression):
        logger.debug(
            'Message: 0x{0:08x} of provider: {1:s} maps to: 0x{2:08x}'.format(
                message_identifier, provider_identifier,
                event_definition.message_identifier))
        message_identifier = event_definition.message_identifier
        break

    message_file_identifiers = []
    for windows_path in provider.event_message_files or []:
      path, filename = path_helper.PathHelper.GetWindowsSystemPath(
          windows_path, self._environment_variables)

      lookup_path = '\\'.join([path, filename]).lower()
      message_file_identifier = self._windows_eventlog_message_files.get(
          lookup_path, None)
      if message_file_identifier:
        message_file_identifier = message_file_identifier.CopyToString()
        message_file_identifiers.append(message_file_identifier)

      mui_filename = '{0:s}.mui'.format(filename)
      lookup_path = '\\'.join([path, self._language_tag, mui_filename]).lower()
      message_file_identifier = self._windows_eventlog_message_files.get(
          lookup_path, None)
      if message_file_identifier:
        message_file_identifier = message_file_identifier.CopyToString()
        message_file_identifiers.append(message_file_identifier)

    if not message_file_identifiers:
      logger.warning(
          'No message file for message: 0x{0:08x} of provider: {1:s}'.format(
              message_identifier, lookup_key))
      return None

    message_strings = []
    # TODO: add message_file_identifiers to filter_expression
    filter_expression = (
        'language_identifier == {0:d} and '
        'message_identifier == {1:d}').format(
            self._lcid, message_identifier)

    for message_string in storage_reader.GetAttributeContainers(
        'windows_eventlog_message_string',
        filter_expression=filter_expression):
      identifier = message_string.GetMessageFileIdentifier()
      identifier = identifier.CopyToString()
      if identifier in message_file_identifiers:
        message_strings.append(message_string)

    if not message_strings:
      logger.warning((
          'No message string for message: 0x{0:08x} of provider: '
          '{1:s}').format(message_identifier, lookup_key))
      return None

    return message_strings[0].string

  def _ReadWindowsEventLogProviders(self, storage_reader):
    """Reads the Windows EventLog providers.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    # TODO: get windows eventlog providers to the source.
    self._windows_eventlog_providers = {}
    if storage_reader.HasAttributeContainers('windows_eventlog_provider'):
      for provider in storage_reader.GetAttributeContainers(
          'windows_eventlog_provider'):

        if provider.identifier:
          self._windows_eventlog_providers[provider.identifier] = provider

        for log_source in provider.log_sources:
          log_source = log_source.lower()
          self._windows_eventlog_providers[log_source] = provider

  def GetMessageString(
      self, provider_identifier, log_source, message_identifier, event_version):
    """Retrieves a specific Windows EventLog message string.

    Args:
      provider_identifier (str): EventLog provider identifier.
      log_source (str): EventLog source, such as "Application Error".
      message_identifier (int): message identifier.
      event_version (int): event version or None if not set.

    Returns:
      str: message string or None if not available.
    """
    message_string = self._GetCachedMessageString(
        provider_identifier, log_source, message_identifier, event_version)
    if not message_string:
      # TODO: change this logic.
      if self._storage_reader and self._storage_reader.HasAttributeContainers(
          'windows_eventlog_provider'):
        message_string = self._ReadWindowsEventLogMessageString(
            self._storage_reader, provider_identifier, log_source,
            message_identifier, event_version)
      else:
        message_string = self._GetWinevtRcDatabaseMessageString(
            log_source, message_identifier)

      if message_string:
        self._CacheMessageString(
            provider_identifier, log_source, message_identifier, event_version,
            message_string)

    return message_string
