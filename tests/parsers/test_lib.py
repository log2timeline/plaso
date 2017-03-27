# -*- coding: utf-8 -*-
"""Parser related functions and classes for testing."""

import heapq

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.containers import sessions
from plaso.engine import knowledge_base
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import py2to3
from plaso.parsers import interface
from plaso.parsers import mediator
from plaso.storage import fake_storage

from tests import test_lib as shared_test_lib


class _EventsHeap(object):
  """Events heap."""

  def __init__(self):
    """Initializes an events heap."""
    super(_EventsHeap, self).__init__()
    self._heap = []

  def PopEvent(self):
    """Pops an event from the heap.

    Returns:
      EventObject: event.
    """
    try:
      _, _, _, event = heapq.heappop(self._heap)
      return event

    except IndexError:
      return None

  def PopEvents(self):
    """Pops events from the heap.

    Yields:
      EventObject: event.
    """
    event = self.PopEvent()
    while event:
      yield event
      event = self.PopEvent()

  def PushEvent(self, event):
    """Pushes an event onto the heap.

    Args:
      event (EventObject): event.
    """
    # TODO: replace this work-around for an event "comparable".
    event_values = event.CopyToDict()
    attributes = []
    for attribute_name, attribute_value in sorted(event_values.items()):
      if isinstance(attribute_value, dict):
        attribute_value = sorted(attribute_value.items())

      elif isinstance(attribute_value, py2to3.BYTES_TYPE):
        attribute_value = repr(attribute_value)

      comparable = u'{0:s}: {1!s}'.format(attribute_name, attribute_value)
      attributes.append(comparable)

    comparable = u', '.join(attributes)
    event_values = sorted(event.CopyToDict().items())
    heap_values = (event.timestamp, event.timestamp_desc, comparable, event)
    heapq.heappush(self._heap, heap_values)

  def PushEvents(self, events):
    """Pushes events onto the heap.

    Args:
      events list[EventObject]: events.
    """
    for event in events:
      self.PushEvent(event)


class ParserTestCase(shared_test_lib.BaseTestCase):
  """Parser test case."""

  def _CreateParserMediator(
      self, storage_writer, file_entry=None, knowledge_base_values=None,
      parser_chain=None, timezone=u'UTC'):
    """Creates a parser mediator.

    Args:
      storage_writer (StorageWriter): storage writer.
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
        knowledge_base_object.SetValue(identifier, value)

    knowledge_base_object.SetTimeZone(timezone)

    parser_mediator = mediator.ParserMediator(
        storage_writer, knowledge_base_object)

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
    storage_writer = fake_storage.FakeStorageWriter(session)
    storage_writer.Open()
    return storage_writer

  def _GetSortedEvents(self, events):
    """Retrieves events sorted in a deterministic order.

    Args:
      events (list[EventObject]): events.

    Returns:
      list[EventObject]: sorted events.
    """
    events_heap = _EventsHeap()
    events_heap.PushEvents(events)
    return list(events_heap.PopEvents())

  def _GetShortMessage(self, message_string):
    """Shortens a message string to a maximum of 80 character width.

    Args:
      message_string (str): message string.

    Returns:
      str: short message string, if it is longer than 80 characters it will
           be shortened to it's first 77 characters followed by a "...".
    """
    if len(message_string) > 80:
      return u'{0:s}...'.format(message_string[:77])

    return message_string

  def _ParseFile(
      self, path_segments, parser, knowledge_base_values=None,
      timezone=u'UTC'):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_segments (list[str]): path segments inside the test data directory.
      parser (BaseParser): parser.
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (str): timezone.

    Returns:
      FakeStorageWriter: storage writer.
    """
    path = self._GetTestFilePath(path_segments)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=path)
    return self._ParseFileByPathSpec(
        path_spec, parser, knowledge_base_values=knowledge_base_values,
        timezone=timezone)

  def _ParseFileByPathSpec(
      self, path_spec, parser, knowledge_base_values=None, timezone=u'UTC'):
    """Parses a file with a parser and writes results to a storage writer.

    Args:
      path_spec (dfvfs.PathSpec): path specification.
      parser (BaseParser): parser.
      knowledge_base_values (Optional[dict]): knowledge base values.
      timezone (str): timezone.

    Returns:
      FakeStorageWriter: storage writer.
    """
    storage_writer = self._CreateStorageWriter()
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    parser_mediator = self._CreateParserMediator(
        storage_writer,
        file_entry=file_entry,
        knowledge_base_values=knowledge_base_values,
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
      self.fail(u'Got unsupported parser type: {0:s}'.format(type(parser)))

    return storage_writer

  def _TestGetMessageStrings(
      self, event, expected_message, expected_message_short):
    """Tests the formatting of the message strings.

    This function invokes the GetMessageStrings function of the event
    formatter on the event object and compares the resulting messages
    strings with those expected.

    Args:
      event (EventObject): event.
      expected_message (str): expected message string.
      expected_message_short (str): expected short message string.
    """
    formatter_mediator = formatters_mediator.FormatterMediator(
        data_location=self._DATA_PATH)
    message, message_short = (
        formatters_manager.FormattersManager.GetMessageStrings(
            formatter_mediator, event))
    self.assertEqual(message, expected_message)
    self.assertEqual(message_short, expected_message_short)

  def _TestGetSourceStrings(
      self, event, expected_source, expected_source_short):
    """Tests the formatting of the source strings.

    This function invokes the GetSourceStrings function of the event
    formatter on the event object and compares the resulting source
    strings with those expected.

    Args:
      event (EventObject): event.
      expected_source (str): expected source string.
      expected_source_short (str): expected short source string.
    """
    # TODO: change this to return the long variant first so it is consistent
    # with GetMessageStrings.
    source_short, source = (
        formatters_manager.FormattersManager.GetSourceStrings(event))
    self.assertEqual(source, expected_source)
    self.assertEqual(source_short, expected_source_short)

  def assertDictContains(self, received, expected):
    """Asserts if a dictionary contains every key-value pair as expected.

    Recieved can contain new keys. If any value is a dict, this function is
    called recursively.

    Args:
      received (dict): received dictionary.
      expected (dict): expected dictionary.
    """
    for key, value in expected.items():
      self.assertIn(key, received)

      if isinstance(value, dict):
        self.assertDictEqual(received[key], expected[key])
      else:
        self.assertEqual(value, expected[key])
