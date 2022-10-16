# -*- coding: utf-8 -*-
"""Syslog plugin related functions and classes for testing."""

from plaso.engine import timeliner
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import syslog

from tests.parsers import test_lib


class SyslogPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for Syslog plugins."""

  def _ParseFileWithPlugin(
      self, path_segments, plugin_name, knowledge_base_values=None,
      time_zone_string='UTC'):
    """Parses a syslog file with a specific plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin_name (str): name of the plugin.
      knowledge_base_values (Optional[dict]): knowledge base values.
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

    # AppendToParserChain needs to be run after SetFileEntry.
    parser_mediator.AppendToParserChain('syslog')

    # TODO: only test plugin.
    parser = syslog.SyslogParser()
    parser.EnablePlugins([plugin_name])

    file_object = file_entry.GetFileObject()
    parser.Parse(parser_mediator, file_object)

    event_data_timeliner = timeliner.EventDataTimeliner(
        knowledge_base_object)
    event_data_timeliner.SetPreferredTimeZone(time_zone_string)

    event_data = storage_writer.GetFirstWrittenEventData()
    while event_data:
      event_data_timeliner.ProcessEventData(storage_writer, event_data)

      event_data = storage_writer.GetNextWrittenEventData()

    return storage_writer
