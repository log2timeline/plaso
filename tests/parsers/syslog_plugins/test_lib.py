# -*- coding: utf-8 -*-
"""Syslog plugin related functions and classes for testing."""

from plaso.containers import sessions
from plaso.parsers import syslog
from plaso.storage import fake_storage

from tests.parsers import test_lib


class SyslogPluginTestCase(test_lib.ParserTestCase):
  """The unit test case for Syslog plugins."""

  def _ParseFileWithPlugin(
      self, path_segments, plugin_name, knowledge_base_values=None):
    """Parses a syslog file with a specific plugin.

    Args:
      path_segments: a list of strings containinge the path segments inside
                     the test data directory.
      plugin_name: a string containing the name of the plugin.
      knowledge_base_values: optional dictionary containing the knowledge base
                             values.

    Returns:
      A storage writer object (instance of FakeStorageWriter).
    """
    session = sessions.Session()
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()

    file_entry = self._GetTestFileEntryFromPath(path_segments)
    parser_mediator = self._CreateParserMediator(
        storage_writer, file_entry=file_entry,
        knowledge_base_values=knowledge_base_values)

    parser_object = syslog.SyslogParser()
    parser_object.EnablePlugins([plugin_name])

    file_object = file_entry.GetFileObject()
    try:
      parser_object.Parse(parser_mediator, file_object)
    finally:
      file_object.close()

    return storage_writer
