# -*- coding: utf-8 -*-
"""Syslog plugin related functions and classes for testing."""

from plaso.parsers import syslog
from plaso.storage.fake import writer as fake_writer

from tests.parsers import test_lib


class SyslogPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for Syslog plugins."""

  def _ParseFileWithPlugin(
      self, path_segments, plugin_name, knowledge_base_values=None,
      timezone='UTC'):
    """Parses a syslog file with a specific plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin_name (str): name of the plugin.
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (Optional[str]): time zone.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values,
        timezone=timezone)

    parser = syslog.SyslogParser()
    parser.EnablePlugins([plugin_name])

    file_object = file_entry.GetFileObject()
    parser.Parse(parser_mediator, file_object)

    return storage_writer
