# -*- coding: utf-8 -*-
"""CSV parser."""

import os
import csv

from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager

class CSVFileParser(interface.FileEntryParser):
  """Parses CSV (Comma Separated Values) files."""

  NAME = 'csv'
  DATA_FORMAT = 'CSV (Comma Separated Values)'

  _plugin_classes = {}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    # pylint: disable=redundant-returns-doc
    return None

  def _ParseFileEntryWithPlugin(
    self,
    parser_mediator,
    plugin,
    location,
    display_name):
    """Parses a CSV (Comma Separated Values) file entry with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      plugin (CSVPlugin): CSV parser plugin.
      location (str): location of CSV file.
      display_name (str): display name.
    """
    profiling_name = '/'.join([self.NAME, plugin.NAME])
    plugin_name = plugin.NAME

    parser_mediator.SampleFormatCheckStartTiming(profiling_name)

    try:
      with open(location, newline='', encoding=plugin.ENCODING) as csvfile:
        reader = csv.DictReader(
          csvfile,
          fieldnames=plugin.CSV_FIELDNAMES,
          dialect=plugin.CSV_DIALECT)

        result01 = plugin.CheckRequiredColumns(reader.fieldnames)
        result02 = plugin.CheckRequiredContent(reader)

    finally:
      parser_mediator.SampleFormatCheckStopTiming(profiling_name)

    if not result01:
      logger.debug(
        'Skipped parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin_name))
      return

    if not result02:
      logger.debug(
        'Skipped parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin_name))
      return

    logger.debug(
      'Parsing file: {0:s} with plugin: {1:s}'.format(
        display_name, plugin_name))

    parser_mediator.SampleStartTiming(profiling_name)

    try:
      with open(location, newline='', encoding=plugin.ENCODING) as csvfile:
        reader = csv.DictReader(
          csvfile,
          fieldnames=plugin.CSV_FIELDNAMES,
          dialect=plugin.CSV_DIALECT)
        plugin.UpdateChainAndProcess(parser_mediator, reader=reader)

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
        'plugin: {0:s} unable to parse CSV file: {1:s} with error: '
        '{2!s}').format(plugin_name, display_name, exception))

    finally:
      parser_mediator.SampleStopTiming(profiling_name)

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses a CSV (Comma Separated Values) file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be parsed.
    """
    filename = parser_mediator.GetFilename()
    display_name = parser_mediator.GetDisplayName(file_entry=file_entry)
    split_tup = os.path.splitext(filename)

    if split_tup[1].lower() != ".csv":
      return

    try:
      for plugin in self._plugins_per_name.values():
        if parser_mediator.abort:
          break

        self._ParseFileEntryWithPlugin(
          parser_mediator=parser_mediator,
          plugin=plugin,
          location=file_entry.path_spec.location,
          display_name=display_name)

    except (IOError, ValueError, UnicodeDecodeError, csv.Error) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open file with error: {0!s}'.format(exception))
    return

manager.ParsersManager.RegisterParser(CSVFileParser)
