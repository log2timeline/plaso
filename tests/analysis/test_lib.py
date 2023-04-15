# -*- coding: utf-8 -*-
"""Analysis plugin related functions and classes for testing."""

from plaso.analysis import mediator as analysis_mediator
from plaso.containers import events
from plaso.engine import timeliner
from plaso.parsers import interface as parsers_interface
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib


class AnalysisPluginTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for an analysis plugin."""

  def _AnalyzeEvents(
      self, event_values_list, plugin, user_accounts=None):
    """Analyzes events using the analysis plugin.

    Args:
      event_values_list (list[dict[str, object]]): list of event values.
      plugin (AnalysisPlugin): plugin.
      user_accounts (Optional[list[UserAccountArtifact]]): user accounts.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()

    for user_account in user_accounts or []:
      storage_writer.AddAttributeContainer(user_account)

    test_events = []
    for event, event_data, event_data_stream in (
        containers_test_lib.CreateEventsFromValues(event_values_list)):
      storage_writer.AddAttributeContainer(event_data_stream)

      event_data.SetEventDataStreamIdentifier(event_data_stream.GetIdentifier())
      storage_writer.AddAttributeContainer(event_data)

      event.SetEventDataIdentifier(event_data.GetIdentifier())
      storage_writer.AddAttributeContainer(event)

      test_events.append((event, event_data, event_data_stream))

    mediator = analysis_mediator.AnalysisMediator(
        user_accounts=user_accounts)
    mediator.SetStorageWriter(storage_writer)

    for event, event_data, event_data_stream in test_events:
      plugin.ExamineEvent(mediator, event, event_data, event_data_stream)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAttributeContainer(analysis_report)

    return storage_writer

  def _ParseAndAnalyzeFile(self, path_segments, parser, plugin):
    """Parses and analyzes a file using the parser and analysis plugin.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      plugin (AnalysisPlugin): plugin.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    storage_writer = self._ParseFile(path_segments, parser)
    mediator = analysis_mediator.AnalysisMediator()
    mediator.SetStorageWriter(storage_writer)

    for event in storage_writer.GetSortedEvents():
      event_data = None
      event_data_identifier = event.GetEventDataIdentifier()
      if event_data_identifier:
        event_data = storage_writer.GetAttributeContainerByIdentifier(
            events.EventData.CONTAINER_TYPE, event_data_identifier)

      event_data_stream = None
      if event_data:
        event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()
        if event_data_stream_identifier:
          event_data_stream = storage_writer.GetAttributeContainerByIdentifier(
              events.EventDataStream.CONTAINER_TYPE,
              event_data_stream_identifier)

      plugin.ExamineEvent(mediator, event, event_data, event_data_stream)

    analysis_report = plugin.CompileReport(mediator)
    storage_writer.AddAttributeContainer(analysis_report)

    return storage_writer

  def _ParseFile(self, path_segments, parser):
    """Parses a file using the parser.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator()

    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = self._GetTestFileEntry(path_segments)
    parser_mediator.SetFileEntry(file_entry)

    event_data_stream = events.EventDataStream()
    parser_mediator.ProduceEventDataStream(event_data_stream)

    if isinstance(parser, parsers_interface.FileEntryParser):
      parser.Parse(parser_mediator)

    elif isinstance(parser, parsers_interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      parser.Parse(parser_mediator, file_object)

    else:
      self.fail('Got unexpected parser type: {0!s}'.format(type(parser)))

    self._ProcessEventData(storage_writer)

    return storage_writer

  def _ProcessEventData(self, storage_writer):
    """Generate events from event data.

    Args:
      storage_writer (StorageWriter): storage writer.
    """
    event_data_timeliner = timeliner.EventDataTimeliner(
        data_location=shared_test_lib.DATA_PATH)

    event_data = storage_writer.GetFirstWrittenEventData()
    while event_data:
      event_data_stream_identifier = event_data.GetEventDataStreamIdentifier()

      event_data_stream = None
      if event_data_stream_identifier:
        event_data_stream = storage_writer.GetAttributeContainerByIdentifier(
            events.EventDataStream.CONTAINER_TYPE, event_data_stream_identifier)

      event_data_timeliner.ProcessEventData(
          storage_writer, event_data, event_data_stream)

      event_data = storage_writer.GetNextWrittenEventData()
