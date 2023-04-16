# -*- coding: utf-8 -*-
"""Parser for Extensible Storage Engine (ESE) database files (EDB)."""

import pyesedb

from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import plugins


class ESEDatabase(object):
  """Extensible Storage Engine (ESE) database."""

  def __init__(self):
    """Initializes an Extensible Storage Engine (ESE) database."""
    super(ESEDatabase, self).__init__()
    self._esedb_file = None
    self._table_names = []

  @property
  def tables(self):
    """list[str]: names of all the tables."""
    if not self._table_names:
      for esedb_table in self._esedb_file.tables:
        self._table_names.append(esedb_table.name)

    return self._table_names

  def Close(self):
    """Closes the database."""
    self._esedb_file.close()
    self._esedb_file = None

  def GetTableByName(self, name):
    """Retrieves a table by its name.

    Args:
      name (str): name of the table.

    Returns:
      pyesedb.table: the table with the corresponding name or None if there is
          no table with the name.
    """
    return self._esedb_file.get_table_by_name(name)

  def Open(self, file_object):
    """Opens an Extensible Storage Engine (ESE) database file.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      IOError: if the file-like object cannot be read.
      OSError: if the file-like object cannot be read.
      ValueError: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError('Missing file object.')

    self._esedb_file = pyesedb.file()
    self._esedb_file.open_file_object(file_object)


class ESEDBCache(plugins.BasePluginCache):
  """A cache storing query results for ESEDB plugins."""

  def StoreDictInCache(self, attribute_name, dict_object):
    """Store a dict object in cache.

    Args:
      attribute_name (str): name of the attribute.
      dict_object (dict): dictionary.
    """
    setattr(self, attribute_name, dict_object)


class ESEDBParser(interface.FileObjectParser):
  """Parses Extensible Storage Engine (ESE) database files (EDB)."""

  _INITIAL_FILE_OFFSET = None

  NAME = 'esedb'
  DATA_FORMAT = 'Extensible Storage Engine (ESE) Database File (EDB) format'

  _plugin_classes = {}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'\xef\xcd\xab\x89', offset=4)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an ESE database file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    database = ESEDatabase()

    try:
      database.Open(file_object)
    except (IOError, ValueError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    display_name = parser_mediator.GetDisplayName()

    # Compare the list of available plugin objects.
    cache = ESEDBCache()
    try:
      for plugin_name, plugin in self._plugins_per_name.items():
        if parser_mediator.abort:
          break

        profiling_name = '/'.join([self.NAME, plugin.NAME])

        parser_mediator.SampleFormatCheckStartTiming(profiling_name)

        try:
          result = plugin.CheckRequiredTables(database)
        finally:
          parser_mediator.SampleFormatCheckStopTiming(profiling_name)

        if not result:
          logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
              display_name, plugin_name))
          continue

        logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
            display_name, plugin_name))

        parser_mediator.SampleStartTiming(profiling_name)

        try:
          plugin.UpdateChainAndProcess(
              parser_mediator, cache=cache, database=database)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              'plugin: {0:s} unable to parse ESE database with error: '
              '{1!s}').format(plugin_name, exception))

        finally:
          parser_mediator.SampleStopTiming(profiling_name)

    finally:
      # TODO: explicitly clean up cache.

      database.Close()


manager.ParsersManager.RegisterParser(ESEDBParser)
