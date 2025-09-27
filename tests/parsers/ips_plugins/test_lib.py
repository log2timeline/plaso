# -*- coding: utf-8 -*-
"""IPS file plugin related functions and classes for testing."""

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import ips_parser

from tests.parsers import test_lib


class IPSPluginTestCase(test_lib.ParserTestCase):
  """IPS parser plugin test case."""

  def _OpenIPSFile(self, path_segments):
    """Opens an IPS log file.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
    Returns:
      tuple: containing:
          file_entry (dfvfs.FileEntry): file entry of the IPS log file.
          IPSFile: IPS log file.
    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    file_entry = self._GetTestFileEntry(path_segments)

    file_object = file_entry.GetFileObject()
    text_file_object = text_file.TextFile(file_object)

    ips_file_object = ips_parser.IPSFile()
    ips_file_object.Open(text_file_object)

    return ips_file_object

  def _ParseIPSFileWithPlugin(self, path_segments, plugin):
    """Parses a file as an IPS crash log file and returns an event generator.

    This method will first test if an IPS log file has the required keys
    using plugin.CheckRequiredKeys() and then extracts events using
    plugin.Process().

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      plugin (IPSPlugin): IPS crash log file plugin.

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
    parser_mediator.AppendToParserChain('ips')

    ips_file_object = self._OpenIPSFile(path_segments)

    self.assertTrue(plugin.CheckRequiredKeys(ips_file_object))

    plugin.UpdateChainAndProcess(parser_mediator, ips_file=ips_file_object)

    return storage_writer
