# -*- coding: utf-8 -*-
"""Text parser plugin related functions and classes for testing."""

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser

from tests.parsers import test_lib


class TextPluginTestCase(test_lib.ParserTestCase):
  """Text parser plugin test case."""

  def _ParseTextFileWithPlugin(
      self, path_segments, plugin, knowledge_base_values=None,
      time_zone_string='UTC'):
    """Parses a file as a text log file and returns an event generator.

    This method will first test if a text log file has the required format
    using plugin.CheckRequiredFormat() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (TextPlugin): text log file plugin.
      knowledge_base_values (Optional[dict[str, object]]): knowledge base
          values.
      time_zone_string (Optional[str]): time zone.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    # TODO: move knowledge base time_zone_string into knowledge_base_values.
    knowledge_base_object = self._CreateKnowledgeBase(
        knowledge_base_values=knowledge_base_values,
        time_zone_string=time_zone_string)

    parser_mediator = parsers_mediator.ParserMediator(knowledge_base_object)

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

    file_object = file_entry.GetFileObject()
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING or parser_mediator.codepage)

    text_reader.ReadLines()

    required_format = plugin.CheckRequiredFormat(parser_mediator, text_reader)
    self.assertTrue(required_format)

    plugin.UpdateChainAndProcess(parser_mediator, file_object=file_object)

    if hasattr(plugin, 'GetYearLessLogHelper'):
      year_less_log_helper = plugin.GetYearLessLogHelper()
      parser_mediator.AddYearLessLogHelper(year_less_log_helper)

    return storage_writer
