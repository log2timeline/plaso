# -*- coding: utf-8 -*-
"""Parser for Extensible Storage Engine (ESE) database files (EDB)."""

from __future__ import unicode_literals

import pyesedb

from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import plugins


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
  DESCRIPTION = 'Parser for Extensible Storage Engine (ESE) database files.'

  _plugin_classes = {}

  def _GetTableNames(self, database):
    """Retrieves the table names in a database.

    Args:
      database (pyesedb.file): ESE database.

    Returns:
      list[str]: table names.
    """
    table_names = []
    for esedb_table in database.tables:
      table_names.append(esedb_table.name)

    return table_names

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
    esedb_file = pyesedb.file()

    try:
      esedb_file.open_file_object(file_object)
    except IOError as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
      return

    # Compare the list of available plugin objects.
    cache = ESEDBCache()
    try:
      table_names = frozenset(self._GetTableNames(esedb_file))

      for plugin in self._plugins:
        if parser_mediator.abort:
          break

        if not plugin.required_tables.issubset(table_names):
          continue

        try:
          plugin.UpdateChainAndProcess(
              parser_mediator, cache=cache, database=esedb_file)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              'plugin: {0:s} unable to parse ESE database with error: '
              '{1!s}').format(plugin.NAME, exception))

    finally:
      # TODO: explicitly clean up cache.

      esedb_file.close()


manager.ParsersManager.RegisterParser(ESEDBParser)
