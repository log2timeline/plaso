# -*- coding: utf-8 -*-
"""SQLite parser."""

import os
import sqlite3
import tempfile

from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import plugins


class SQLiteCache(plugins.BasePluginCache):
  """Cache for storing results of SQL queries."""

  def __init__(self):
    """Initializes a SQLite cache."""
    super(SQLiteCache, self).__init__()
    self._row_caches = {}

  def CacheQueryResults(
      self, sql_results, attribute_name, key_name, column_names):
    """Build a dictionary object based on a SQL command.

    This function will take a SQL command, execute it and for
    each resulting row it will store a key in a dictionary.

    An example::

      sql_results = A SQL result object after executing the
                    SQL command: 'SELECT foo, bla, bar FROM my_table'
      attribute_name = 'all_the_things'
      key_name = 'foo'
      column_names = ['bla', 'bar']

    Results from running this against the database:
    'first', 'stuff', 'things'
    'second', 'another stuff', 'another thing'

    This will result in a dictionary object being created in the
    cache, called 'all_the_things' and it will contain the following value::

      all_the_things = {
          'first': ['stuff', 'things'],
          'second': ['another_stuff', 'another_thing'],
          'third': ['single_thing']}

    Args:
      sql_results (sqlite3.Cursor): result after executing a SQL command
          on a database.
      attribute_name (str): attribute name in the cache to store results to.
          This will be the name of the dictionary attribute.
      key_name (str): name of the result field that should be used as a key
          in the resulting dictionary that is created.
      column_names (list[str]): of column names that are stored as values to
          the dictionary. If this list has only one value in it the value will
          be stored directly, otherwise the value will be a list containing
          the extracted results based on the names provided in this list.
    """
    row = sql_results.fetchone()
    if not row:
      return

    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    keys_name_to_index_map = {
        name: index for index, name in enumerate(row.keys())}

    attribute_value = {}
    while row:
      value_index = keys_name_to_index_map.get(key_name)
      key_value = row[value_index]

      attribute_value[key_value] = []
      for column_name in column_names:
        value_index = keys_name_to_index_map.get(column_name)
        column_value = row[value_index]
        attribute_value[key_value].append(column_value)

      row = sql_results.fetchone()

    setattr(self, attribute_name, attribute_value)

  def GetRowCache(self, query):
    """Retrieves the row cache for a specific query.

    The row cache is a set that contains hashes of values in a row. The row
    cache is used to find duplicate row when a database and a database with
    a WAL file is parsed.

    Args:
      query (str): query.

    Returns:
      set: hashes of the rows that have been parsed.
    """
    query_hash = hash(query)
    if query_hash not in self._row_caches:
      self._row_caches[query_hash] = set()
    return self._row_caches[query_hash]


class SQLiteDatabase(object):
  """SQLite database.

  Attributes:
    schema (dict[str, str]): schema as an SQL query per table name, for
        example {'Users': 'CREATE TABLE Users ("id" INTEGER PRIMARY KEY, ...)'}.
  """

  _READ_BUFFER_SIZE = 65536

  SCHEMA_QUERY = (
      'SELECT tbl_name, sql '
      'FROM sqlite_master '
      'WHERE type = "table" AND tbl_name != "xp_proc" '
      'AND tbl_name != "sqlite_sequence"')

  def __init__(self, filename, temporary_directory=None):
    """Initializes a SQLite database.

    Args:
      filename (str): name of the file entry.
      temporary_directory (Optional[str]): path of the directory for temporary
          files.
    """
    super(SQLiteDatabase, self).__init__()
    self._database = None
    self._filename = filename
    self._temp_db_file_path = ''
    self._temporary_directory = temporary_directory
    self._temp_wal_file_path = ''

    self.schema = {}
    self.columns_per_table = {}

  @property
  def tables(self):
    """list[str]: names of all the tables."""
    return self.schema.keys()

  def _CopyFileObjectToTemporaryFile(self, file_object, temporary_file):
    """Copies the contents of the file-like object to a temporary file.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      temporary_file (file): temporary file.
    """
    file_object.seek(0, os.SEEK_SET)
    data = file_object.read(self._READ_BUFFER_SIZE)
    while data:
      temporary_file.write(data)
      data = file_object.read(self._READ_BUFFER_SIZE)

  def Close(self):
    """Closes the database connection and cleans up the temporary file."""
    self.schema = {}
    self._database = None

    if os.path.exists(self._temp_db_file_path):
      try:
        os.remove(self._temp_db_file_path)
      except (OSError, IOError) as exception:
        logger.warning((
            'Unable to remove temporary copy: {0:s} of SQLite database: '
            '{1:s} with error: {2!s}').format(
                self._temp_db_file_path, self._filename, exception))

    self._temp_db_file_path = ''

    if os.path.exists(self._temp_wal_file_path):
      try:
        os.remove(self._temp_wal_file_path)
      except (OSError, IOError) as exception:
        logger.warning((
            'Unable to remove temporary copy: {0:s} of SQLite database: '
            '{1:s} with error: {2!s}').format(
                self._temp_wal_file_path, self._filename, exception))

    self._temp_wal_file_path = ''

  def Open(self, file_object, wal_file_object=None):
    """Opens a SQLite database file.

    Since pysqlite cannot read directly from a file-like object a temporary
    copy of the file is made. After creating a copy the database file this
    function sets up a connection with the database and determines the names
    of the tables.

    Args:
      file_object (dfvfs.FileIO): file-like object.
      wal_file_object (Optional[dfvfs.FileIO]): file-like object for the
          Write-Ahead Log (WAL) file.

    Raises:
      IOError: if the file-like object cannot be read.
      OSError: if the file-like object cannot be read.
      sqlite3.DatabaseError: if the database cannot be parsed.
      ValueError: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError('Missing file object.')

    # TODO: Current design copies the entire file into a buffer
    # that is parsed by each SQLite parser. This is not very efficient,
    # especially when many SQLite parsers are ran against a relatively
    # large SQLite database. This temporary file that is created should
    # be usable by all SQLite parsers so the file should only be read
    # once in memory and then deleted when all SQLite parsers have completed.

    # TODO: Change this into a proper implementation using APSW
    # and virtual filesystems when that will be available.
    # Info: http://apidoc.apsw.googlecode.com/hg/vfs.html#vfs and
    # http://apidoc.apsw.googlecode.com/hg/example.html#example-vfs
    # Until then, just copy the file into a tempfile and parse it.

    with tempfile.NamedTemporaryFile(
        delete=False, dir=self._temporary_directory) as temporary_file:
      try:
        self._CopyFileObjectToTemporaryFile(file_object, temporary_file)
        self._temp_db_file_path = temporary_file.name

      except IOError:
        os.remove(temporary_file.name)
        raise

    if wal_file_object:
      # Create WAL file using same filename so it is available for
      # sqlite3.connect()
      temporary_filename = '{0:s}-wal'.format(self._temp_db_file_path)

      with open(temporary_filename, 'wb') as temporary_file:
        try:
          self._CopyFileObjectToTemporaryFile(wal_file_object, temporary_file)
          self._temp_wal_file_path = temporary_filename

        except IOError:
          os.remove(temporary_filename)
          raise

    self._database = sqlite3.connect(self._temp_db_file_path)
    try:
      self._database.row_factory = sqlite3.Row
      cursor = self._database.cursor()

      sql_results = cursor.execute(self.SCHEMA_QUERY)

      self.schema = {
          table_name: ' '.join(query.split())
          for table_name, query in sql_results}

      for table_name in self.schema.keys():
        self.columns_per_table.setdefault(table_name, [])

        # The table name needs to be enclosed in quotes in case it contains
        # special characters like a dot.
        pragma_results = cursor.execute(
            'PRAGMA table_info("{0:s}")'.format(table_name))

        for pragma_result in pragma_results:
          self.columns_per_table[table_name].append(pragma_result['name'])

    except sqlite3.DatabaseError as exception:
      self._database.close()
      self._database = None

      os.remove(self._temp_db_file_path)
      self._temp_db_file_path = ''
      if self._temp_wal_file_path:
        os.remove(self._temp_wal_file_path)
        self._temp_wal_file_path = ''

      logger.debug(
          'Unable to parse SQLite database: {0:s} with error: {1!s}'.format(
              self._filename, exception))
      raise

  def Query(self, query):
    """Queries the database.

    Args:
      query (str): SQL query.

    Returns:
      sqlite3.Cursor: results.

    Raises:
      sqlite3.DatabaseError: if querying the database fails.
    """
    cursor = self._database.cursor()
    cursor.execute(query)
    return cursor


class SQLiteParser(interface.FileEntryParser):
  """Parses SQLite database files."""

  NAME = 'sqlite'
  DATA_FORMAT = 'SQLite database file'

  _plugin_classes = {}

  def _OpenDatabaseWithWAL(
      self, parser_mediator, database_file_entry, database_file_object,
      filename):
    """Opens a database with its Write-Ahead Log (WAL) committed.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      database_file_entry (dfvfs.FileEntry): file entry of the database.
      database_file_object (dfvfs.FileIO): file-like object of the database.
      filename (str): name of the database file entry.

    Returns:
      tuple: containing:

        SQLiteDatabase: a database object with WAL file committed or None
        dfvfs.FileEntry: a file entry object of WAL file or None
    """
    path_spec = database_file_entry.path_spec
    location = getattr(path_spec, 'location', None)
    if not path_spec or not location:
      return None, None

    location_wal = '{0:s}-wal'.format(location)
    file_system = database_file_entry.GetFileSystem()
    wal_path_spec = path_spec_factory.Factory.NewPathSpec(
        file_system.type_indicator, parent=path_spec.parent,
        location=location_wal)

    wal_file_entry = file_system.GetFileEntryByPathSpec(wal_path_spec)
    if not wal_file_entry:
      return None, None

    wal_file_object = wal_file_entry.GetFileObject()
    if not wal_file_object:
      return None, None

    database_wal = SQLiteDatabase(
        filename, temporary_directory=parser_mediator.temporary_directory)

    try:
      database_wal.Open(database_file_object, wal_file_object=wal_file_object)

    except (IOError, ValueError, sqlite3.DatabaseError) as exception:
      parser_mediator.ProduceExtractionWarning((
          'unable to open SQLite database and WAL with error: '
          '{0!s}').format(exception))

      return None, None

    return database_wal, wal_file_entry

  def _ParseFileEntryWithPlugin(
      self, parser_mediator, plugin, database, display_name, cache):
    """Parses a SQLite database file entry with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      plugin (SQLitePlugin): SQLite parser plugin.
      database (SQLiteDatabase): database.
      display_name (str): display name.
      cache (SQLiteCache): cache.
    """
    profiling_name = '/'.join([self.NAME, plugin.NAME])

    parser_mediator.SampleFormatCheckStartTiming(profiling_name)

    try:
      result = plugin.CheckRequiredTablesAndColumns(database)
    finally:
      parser_mediator.SampleFormatCheckStopTiming(profiling_name)

    if not result:
      logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin.NAME))
      return

    logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
        display_name, plugin.NAME))

    parser_mediator.SampleStartTiming(profiling_name)

    try:
      schema_match = plugin.CheckSchema(database)
      if plugin.REQUIRES_SCHEMA_MATCH and not schema_match:
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} found required tables but not a matching '
            'schema').format(plugin.NAME))
      else:
        plugin.UpdateChainAndProcess(
            parser_mediator, cache=cache, database=database)

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'plugin: {0:s} unable to parse SQLite database with error: '
          '{1!s}').format(plugin.NAME, exception))

    finally:
      parser_mediator.SampleStopTiming(profiling_name)

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'SQLite format 3', offset=0)
    return format_specification

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses a SQLite database file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be parsed.
    """
    filename = parser_mediator.GetFilename()
    database = SQLiteDatabase(
        filename, temporary_directory=parser_mediator.temporary_directory)

    file_object = file_entry.GetFileObject()
    try:
      database.Open(file_object)

    except (IOError, ValueError, sqlite3.DatabaseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open SQLite database with error: {0!s}'.format(exception))
      return

    # Create a cache in which the resulting tables are cached.
    cache = SQLiteCache()

    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)

    try:
      for plugin in self._plugins_per_name.values():
        self._ParseFileEntryWithPlugin(
            parser_mediator, plugin, database, display_name, cache)
    finally:
      database.Close()

    database_wal, wal_file_entry = self._OpenDatabaseWithWAL(
        parser_mediator, file_entry, file_object, filename)

    if not database_wal:
      return

    # Note that SetFileEntry will reset the current event data stream in
    # the parser mediator.
    parser_mediator.SetFileEntry(wal_file_entry)

    event_data_stream = events.EventDataStream()
    event_data_stream.path_spec = wal_file_entry.path_spec

    parser_mediator.ProduceEventDataStream(event_data_stream)

    # Create a cache in which the resulting tables are cached.
    cache = SQLiteCache()

    display_name = parser_mediator.GetDisplayName(file_entry=wal_file_entry)

    try:
      for plugin in self._plugins_per_name.values():
        self._ParseFileEntryWithPlugin(
            parser_mediator, plugin, database_wal, display_name, cache)
    finally:
      database_wal.Close()


manager.ParsersManager.RegisterParser(SQLiteParser)
