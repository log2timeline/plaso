# -*- coding: utf-8 -*-
"""Parser related functions and classes for testing."""

from __future__ import unicode_literals

import os

from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.parsers import interface
from plaso.parsers import mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class ParserTestCase(shared_test_lib.BaseTestCase):
  """Parser test case."""

  def _CreateParserMediator(
      self, storage_writer, collection_filters_helper=None, file_entry=None,
      knowledge_base_values=None, parser_chain=None, timezone='UTC'):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
      collection_filters_helper (Optional[CollectionFiltersHelper]): collection
          filters helper.
      file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.
      knowledge_base_values (Optional[dict]): knowledge base values.
      parser_chain (Optional[str]): parsing chain up to this point.
      timezone (str): timezone.

    Returns:
      ParserMediator: parser mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()
    if knowledge_base_values:
      for identifier, value in iter(knowledge_base_values.items()):
        if identifier == 'codepage':
          knowledge_base_object.SetCodepage(value)
        else:
          knowledge_base_object.SetValue(identifier, value)

    knowledge_base_object.SetTimeZone(timezone)

    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object,
        collection_filters_helper=collection_filters_helper)

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
    session = sessions.Session()
    storage_writer = fake_writer.FakeStorageWriter(session)
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
    return storage_writer.GetEventDataByIdentifier(event_data_identifier)

  def _GetShortMessage(self, message_string):
    """Shortens a message string to a maximum of 80 character width.

    Args:
      message_string (str): message string.

    Returns:
      str: short message string, if it is longer than 80 characters it will
           be shortened to it's first 77 characters followed by a "...".
    """
    if len(message_string) > 80:
      return '{0:s}...'.format(message_string[:77])

    return message_string

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
      timezone (str): timezone.

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
      timezone (str): timezone.

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
      try:
        parser.Parse(parser_mediator, file_object)
      finally:
        file_object.close()

    else:
      self.fail('Got unsupported parser type: {0:s}'.format(type(parser)))

    return storage_writer

  def _TestGetMessageStrings(
      self, event_data, expected_message, expected_short_message):
    """Tests the formatting of the message strings.

    This function invokes the GetMessageStrings function of the event data
    formatter on the event data and compares the resulting messages strings
    with those expected.

    Args:
      event_data (EventData): event data.
      expected_message (str): expected message string.
      expected_short_message (str): expected short message string.
    """
    formatters_file_path = os.path.join(self._DATA_PATH, 'formatters.yaml')
    formatters_manager.FormattersManager.ReadFormattersFromFile(
        formatters_file_path)

    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._DATA_PATH)
    message, message_short = (
        formatters_manager.FormattersManager.GetMessageStrings(
            formatter_mediator, event_data))
    self.assertEqual(message, expected_message)
    self.assertEqual(message_short, expected_short_message)

  def _TestGetSourceStrings(
      self, event, event_data, expected_source, expected_source_short):
    """Tests the formatting of the source strings.

    This function invokes the GetSourceStrings function of the event
    formatter on the event and compares the resulting source
    strings with those expected.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      expected_source (str): expected source string.
      expected_source_short (str): expected short source string.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    source_short, source = (
        formatters_manager.FormattersManager.GetSourceStrings(
            event, event_data))
    self.assertEqual(source, expected_source)
    self.assertEqual(source_short, expected_source_short)

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
