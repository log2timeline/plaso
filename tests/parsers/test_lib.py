# -*- coding: utf-8 -*-
"""Parser related functions and classes for testing."""

from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.file_io import fake_file_io
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
from plaso.engine import knowledge_base
from plaso.parsers import interface
from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class ParserTestCase(shared_test_lib.BaseTestCase):
  """Parser test case."""

  def _CreateFileObject(self, filename, data):
    """Creates a file-like object.

    Args:
      filename (str): name of the file.
      data (bytes): data of the file.

    Returns:
      dfvfs.FakeFile: file-like object.
    """
    resolver_context = dfvfs_context.Context()

    location = '/{0:s}'.format(filename)
    test_path_spec = fake_path_spec.FakePathSpec(location=location)
    file_object = fake_file_io.FakeFile(resolver_context, test_path_spec, data)
    file_object.Open()

    return file_object

  def _CreateParserMediator(
      self, storage_writer, collection_filters_helper=None,
      file_entry=None, knowledge_base_values=None, parser_chain=None,
      timezone='UTC'):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      collection_filters_helper (Optional[CollectionFiltersHelper]): collection
          filters helper.
      file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.
      knowledge_base_values (Optional[dict]): knowledge base values.
      parser_chain (Optional[str]): parsing chain up to this point.
      timezone (Optional[str]): timezone.

    Returns:
      ParserMediator: parser mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in knowledge_base_values.items():
        if identifier == 'codepage':
          knowledge_base_object.SetCodepage(value)
        else:
          knowledge_base_object.SetValue(identifier, value)

    knowledge_base_object.SetTimeZone(timezone)

    parser_mediator = parsers_mediator.ParserMediator(
        knowledge_base_object,
        collection_filters_helper=collection_filters_helper)
    parser_mediator.SetStorageWriter(storage_writer)

    if file_entry:
      parser_mediator.SetFileEntry(file_entry)

    if parser_chain:
      parser_mediator.parser_chain = parser_chain

    return parser_mediator

  def _CreateStorageWriter(self):
    """Creates a storage writer object.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = fake_writer.FakeStorageWriter()
    storage_writer.Open()
    return storage_writer

  def _GetEventDataOfEvent(self, storage_writer, event):
    """Retrieves the event data of an event.

    Args:
      storage_writer (FakeStorageWriter): storage writer.
      event (EventObject): event.

    Return:
      EventData: event data corresponding to the event.
    """
    event_data_identifier = event.GetEventDataIdentifier()
    return storage_writer.GetAttributeContainerByIdentifier(
        events.EventData.CONTAINER_TYPE, event_data_identifier)

  def _ParseFile(
      self, path_segments, parser, collection_filters_helper=None,
      knowledge_base_values=None, timezone='UTC'):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      collection_filters_helper (Optional[CollectionFiltersHelper]): collection
          filters helper.
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (Optional[str]): time zone.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    test_file_path = self._GetTestFilePath(path_segments)
    self._SkipIfPathNotExists(test_file_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=test_file_path)
    return self._ParseFileByPathSpec(
        path_spec, parser, collection_filters_helper=collection_filters_helper,
        knowledge_base_values=knowledge_base_values, timezone=timezone)

  def _ParseFileByPathSpec(
      self, path_spec, parser, collection_filters_helper=None,
      knowledge_base_values=None, timezone='UTC'):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      parser (BaseParser): parser.
      collection_filters_helper (Optional[CollectionFiltersHelper]): collection
          filters helper.
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (Optional[str]): time zone.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = self._CreateStorageWriter()
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator = self._CreateParserMediator(
        storage_writer, collection_filters_helper=collection_filters_helper,
        file_entry=file_entry, knowledge_base_values=knowledge_base_values,
        timezone=timezone)

    if isinstance(parser, interface.FileEntryParser):
      parser.Parse(parser_mediator)

    elif isinstance(parser, interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      parser.Parse(parser_mediator, file_object)

    else:
      self.fail('Got unsupported parser type: {0!s}'.format(type(parser)))

    return storage_writer

  def CheckEventValues(self, storage_writer, event, expected_event_values):
    """Asserts that an event and its event data matches the expected values.

    Args:
      storage_writer (StorageWriter): storage writer.
      event (EventObject): event to check.
      expected_event_values (dict[str, list[str]): expected values of the event
          and event data attribute values per name.
    """
    event_data = None
    for name, expected_value in expected_event_values.items():
      if name == 'timestamp' and isinstance(expected_value, str):
        posix_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=event.timestamp)
        value = posix_time.CopyToDateTimeString()

      elif name in ('date_time', 'timestamp', 'timestamp_desc'):
        value = getattr(event, name, None)

      else:
        if not event_data:
          event_data = self._GetEventDataOfEvent(storage_writer, event)

        value = getattr(event_data, name, None)

      if name == 'date_time' and value and isinstance(expected_value, str):
        value = value.CopyToDateTimeString()

      error_message = (
          'event value: "{0:s}" does not match expected value').format(name)
      self.assertEqual(value, expected_value, error_message)

  def CheckTimestamp(self, timestamp, expected_date_time):
    """Asserts that a timestamp value matches the expected date and time.

    Args:
      timestamp (int): timestamp, which contains the number of microseconds
          since January 1, 1970, 00:00:00 UTC.
      expected_date_time (str): expected date and time in UTC, formatted as:
          YYYY-MM-DD hh:mm:ss.######
    """
    posix_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=timestamp)
    date_time = posix_time.CopyToDateTimeString()
    self.assertEqual(date_time, expected_date_time)
