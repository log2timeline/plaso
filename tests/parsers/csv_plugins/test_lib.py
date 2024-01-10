# -*- coding: utf-8 -*-
"""CSV file plugin related functions and classes for testing."""

import csv

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator

from tests.parsers import test_lib

class CSVPluginTestCase(test_lib.ParserTestCase):
  """CSV file plugin test case."""

  def _ParseCSVFileWithPlugin(self, path_segments, plugin):
    """Parses a file as a CSV file and return an event generator.
    
    This method will first test if a CSV file contains the required
    columns using plugin.CheckRequiredColumns() and required content 
    using plugin.CheckRequiredContent() and then extracts events
    using plugin.Process().
    
    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (CSVPlugin): compound ZIP file plugin.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('csv')

    print()
    with open(
      file_entry.path_spec.location,
      newline='',
      encoding=plugin.ENCODING) as csvfile:
      reader = csv.DictReader(
          csvfile,
          fieldnames=plugin.CSV_FIELDNAMES,
          dialect=plugin.CSV_DIALECT)

      result01 = plugin.CheckRequiredColumns(reader.fieldnames)
      self.assertTrue(result01)

      result02 = plugin.CheckRequiredContent(reader)
      self.assertTrue(result02)

    with open(
      file_entry.path_spec.location,
      newline='',
      encoding=plugin.ENCODING) as csvfile:
      reader = csv.DictReader(
          csvfile,
          fieldnames=plugin.CSV_FIELDNAMES,
          dialect=plugin.CSV_DIALECT)
      plugin.UpdateChainAndProcess(parser_mediator, reader=reader)

    return storage_writer
