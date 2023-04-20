# -*- coding: utf-8 -*-
"""Parser related functions and classes for testing."""

from dfdatetime import interface as dfdatetime_interface
from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.file_io import fake_file_io
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import events
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

  def _CreateParserMediator(self, storage_writer, file_entry=None):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.

    Returns:
      ParserMediator: parser mediator.
    """
    parser_mediator = parsers_mediator.ParserMediator()
    parser_mediator.SetStorageWriter(storage_writer)

    if file_entry:
      parser_mediator.SetFileEntry(file_entry)

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

  def _ParseFile(self, path_segments, parser, registry_find_specs=None):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      registry_find_specs (Optional[list[dfwinreg.FindSpec]]): Windows Registry
          find specifications.

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
        path_spec, parser, registry_find_specs=registry_find_specs)

  def _ParseFileByPathSpec(self, path_spec, parser, registry_find_specs=None):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      parser (BaseParser): parser.
      registry_find_specs (Optional[list[dfwinreg.FindSpec]]): Windows Registry
          find specifications.

    Returns:
      FakeStorageWriter: storage writer.

    Raises:
      SkipTest: if the path inside the test data directory does not exist and
          the test should be skipped.
    """
    parser_mediator = parsers_mediator.ParserMediator(
        registry_find_specs=registry_find_specs)

    storage_writer = self._CreateStorageWriter()
    parser_mediator.SetStorageWriter(storage_writer)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator.SetFileEntry(file_entry)

    if file_entry:
      event_data_stream = events.EventDataStream()
      event_data_stream.path_spec = file_entry.path_spec

      parser_mediator.ProduceEventDataStream(event_data_stream)

    if isinstance(parser, interface.FileEntryParser):
      parser.Parse(parser_mediator)

    elif isinstance(parser, interface.FileObjectParser):
      file_object = file_entry.GetFileObject()
      parser.Parse(parser_mediator, file_object)

    else:
      parser_type = type(parser)
      self.fail('Unsupported parser type: {0!s}'.format(parser_type))

    return storage_writer

  def CheckEventData(self, event_data, expected_event_values):
    """Asserts that event data matches the expected values.

    Args:
      event_data (EventData): event data to check.
      expected_event_values (dict[str, list[str]): expected values of the event
          data attribute values per name.
    """
    for name, expected_value in expected_event_values.items():
      value = getattr(event_data, name, None)
      if isinstance(value, dfdatetime_interface.DateTimeValues):
        date_time_value = value.CopyToDateTimeStringISO8601()
        if not date_time_value:
          # Call CopyToDateTimeString to support semantic date time values.
          date_time_value = value.CopyToDateTimeString()
        value = date_time_value

      elif isinstance(value, list) and value and isinstance(
          value[0], dfdatetime_interface.DateTimeValues):
        value = [date_time_value.CopyToDateTimeStringISO8601()
                 for date_time_value in value]

      error_message = (
          'event value: "{0:s}" does not match expected value').format(name)
      self.assertEqual(value, expected_value, error_message)

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
        date_time_value = value.CopyToDateTimeStringISO8601()
        if not date_time_value:
          # Call CopyToDateTimeString to support semantic date time values.
          date_time_value = value.CopyToDateTimeString()
        value = date_time_value

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
