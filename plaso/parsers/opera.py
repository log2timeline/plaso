# -*- coding: utf-8 -*-
"""Parsers for Opera Browser history files."""

from __future__ import unicode_literals

import os

try:
  import urlparse
except ImportError:
  from urllib import parse as urlparse

# pylint: disable=wrong-import-position
from defusedxml import ElementTree
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements
from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager


class OperaTypedHistoryEventData(events.EventData):
  """Opera typed history entry data.

  Attributes:
    entry_selection (str): information about whether the URL was directly
        typed in or the result of the user choosing from the auto complete.
    entry_type (str): information about whether the URL was directly typed in
        or the result of the user choosing from the auto complete.
    url (str): typed URL or hostname.
  """

  DATA_TYPE = 'opera:history:typed_entry'

  def __init__(self):
    """Initializes event data."""
    super(OperaTypedHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_selection = None
    self.entry_type = None
    self.url = None


class OperaGlobalHistoryEventData(events.EventData):
  """Opera global history entry data.

  Attributes:
    description (str): description.
    popularity_index (int): popularity index.
    title (str): title.
    url (str):  URL.
  """

  DATA_TYPE = 'opera:history:entry'

  def __init__(self):
    """Initializes event data."""
    super(OperaGlobalHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.popularity_index = None
    self.title = None
    self.url = None


class OperaTypedHistoryParser(interface.FileObjectParser):
  """Parses the Opera typed_history.xml file."""

  NAME = 'opera_typed_history'
  DESCRIPTION = 'Parser for Opera typed_history.xml files.'

  _HEADER_READ_SIZE = 128

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Opera typed history file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    data = file_object.read(self._HEADER_READ_SIZE)
    if not data.startswith(b'<?xml'):
      raise errors.UnableToParseFile(
          'Not an Opera typed history file [not a XML]')

    _, _, data = data.partition(b'\n')
    if not data.startswith(b'<typed_history'):
      raise errors.UnableToParseFile(
          'Not an Opera typed history file [wrong XML root key]')

    # For ElementTree to work we need to work on a file object seeked
    # to the beginning.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)

    for history_item in xml.iterfind('typed_history_item'):
      event_data = OperaTypedHistoryEventData()
      event_data.entry_type = history_item.get('type', None)
      event_data.url = history_item.get('content', None)

      if event_data.entry_type == 'selected':
        event_data.entry_selection = 'Filled from autocomplete.'
      elif event_data.entry_type == 'text':
        event_data.entry_selection = 'Manually typed.'

      last_typed_time = history_item.get('last_typed', None)
      if last_typed_time is None:
        parser_mediator.ProduceExtractionWarning('missing last typed time.')
        continue

      date_time = dfdatetime_time_elements.TimeElements()

      try:
        date_time.CopyFromStringISO8601(last_typed_time)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning(
            'unsupported last typed time: {0:s} with error: {1!s}.'.format(
                last_typed_time, exception))
        continue

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


class OperaGlobalHistoryParser(interface.FileObjectParser):
  """Parses the Opera global_history.dat file."""

  NAME = 'opera_global'
  DESCRIPTION = 'Parser for Opera global_history.dat files.'

  _ENCODING = 'utf-8'

  _MAXIMUM_LINE_SIZE = 512

  _SUPPORTED_URL_SCHEMES = frozenset(['file', 'http', 'https', 'ftp'])

  def _IsValidUrl(self, url):
    """Checks if an URL is considered valid.

    Returns:
      bool: True if the URL is valid.
    """
    parsed_url = urlparse.urlparse(url)
    return parsed_url.scheme in self._SUPPORTED_URL_SCHEMES

  def _ParseRecord(self, parser_mediator, text_file_object):
    """Parses an Opera global history record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if the record was successfully parsed.
    """
    try:
      title = text_file_object.readline()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to read and decode title')
      return False

    if not title:
      return False

    try:
      url = text_file_object.readline()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to read and decode url')
      return False

    try:
      timestamp = text_file_object.readline()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to read and decode timestamp')
      return False

    try:
      popularity_index = text_file_object.readline()
    except UnicodeDecodeError:
      parser_mediator.ProduceExtractionWarning(
          'unable to read and decode popularity index')
      return False

    event_data = OperaGlobalHistoryEventData()

    event_data.url = url.strip()

    title = title.strip()
    if title != event_data.url:
      event_data.title = title

    popularity_index = popularity_index.strip()
    try:
      event_data.popularity_index = int(popularity_index, 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unable to convert popularity index: {0:s}'.format(popularity_index))

    if event_data.popularity_index < 0:
      event_data.description = 'First and Only Visit'
    else:
      event_data.description = 'Last Visit'

    timestamp = timestamp.strip()
    try:
      timestamp = int(timestamp, 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unable to convert timestamp: {0:s}'.format(timestamp))
      timestamp = None

    if timestamp is None:
      date_time = dfdatetime_semantic_time.SemanticTime('Invalid')
    else:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return True

  def _ParseAndValidateRecord(self, parser_mediator, text_file_object):
    """Parses and validates an Opera global history record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      text_file_object (dfvfs.TextFile): text file.

    Returns:
      bool: True if the record was successfully parsed.
    """
    try:
      title = text_file_object.readline(size=self._MAXIMUM_LINE_SIZE)
      url = text_file_object.readline(size=self._MAXIMUM_LINE_SIZE)
      timestamp = text_file_object.readline(size=self._MAXIMUM_LINE_SIZE)
      popularity_index = text_file_object.readline(size=self._MAXIMUM_LINE_SIZE)
    except UnicodeDecodeError:
      return False

    if len(title) == self._MAXIMUM_LINE_SIZE and title[-1] != '\n':
      return False

    if len(url) == self._MAXIMUM_LINE_SIZE and url[-1] != '\n':
      return False

    if len(timestamp) == self._MAXIMUM_LINE_SIZE and timestamp[-1] != '\n':
      return False

    if (len(popularity_index) == self._MAXIMUM_LINE_SIZE and
        popularity_index[-1] != '\n'):
      return False

    title = title.strip()
    url = url.strip()
    timestamp = timestamp.strip()
    popularity_index = popularity_index.strip()

    if not title or not url or not timestamp or not popularity_index:
      return False

    event_data = OperaGlobalHistoryEventData()

    if not self._IsValidUrl(url):
      return False

    event_data.url = url
    if title != url:
      event_data.title = title

    try:
      event_data.popularity_index = int(popularity_index, 10)
      timestamp = int(timestamp, 10)
    except ValueError:
      return False

    if event_data.popularity_index < 0:
      event_data.description = 'First and Only Visit'
    else:
      event_data.description = 'Last Visit'

    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    return True

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Opera global history file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    encoding = self._ENCODING or parser_mediator.codepage
    text_file_object = text_file.TextFile(file_object, encoding=encoding)
    if not self._ParseAndValidateRecord(parser_mediator, text_file_object):
      raise errors.UnableToParseFile(
          'Unable to parse as Opera global_history.dat.')

    while self._ParseRecord(parser_mediator, text_file_object):
      pass


manager.ParsersManager.RegisterParsers([
    OperaTypedHistoryParser, OperaGlobalHistoryParser])
