# -*- coding: utf-8 -*-
"""Text parser plugin related functions and classes for testing."""

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser

from tests.parsers import test_lib


class TextPluginTestCase(test_lib.ParserTestCase):
  """Text parser plugin test case."""

  def _ParseTextFileWithPlugin(self, path_segments, plugin):
    """Parses a file as a text log file and returns an event generator.

    This method will first test if a text log file has the required format
    using plugin.CheckRequiredFormat() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (TextPlugin): text log file plugin.

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
    parser_mediator.AppendToParserChain('text')

    encoding = plugin.ENCODING
    if not encoding:
      encoding = parser_mediator.GetCodePage()

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(file_object, encoding=encoding)

    text_reader.ReadLines()

    required_format = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(required_format)

    plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

    if hasattr(plugin, 'GetYearLessLogHelper'):
      year_less_log_helper = plugin.GetYearLessLogHelper()
      parser_mediator.AddYearLessLogHelper(year_less_log_helper)

    return storage_writer
