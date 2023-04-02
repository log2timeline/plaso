# -*- coding: utf-8 -*-
"""Parsers for Opera Browser history files."""

import os

from urllib import parse as urlparse

from defusedxml import ElementTree
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements
from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class OperaGlobalHistoryEventData(events.EventData):
  """Opera global history entry data.

  Attributes:
    description (str): description.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    popularity_index (int): popularity index.
    title (str): title.
    url (str):  URL.
  """

  DATA_TYPE = 'opera:history:entry'

  def __init__(self):
    """Initializes event data."""
    super(OperaGlobalHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.last_visited_time = None
    self.popularity_index = None
    self.title = None
    self.url = None


class OperaTypedHistoryEventData(events.EventData):
  """Opera typed history entry data.

  Attributes:
    entry_selection (str): information about whether the URL was directly
        typed in or the result of the user choosing from the auto complete.
    entry_type (str): information about whether the URL was directly typed in
        or the result of the user choosing from the auto complete.
    last_typed_time (dfdatetime.DateTimeValues): date and time the URL was
        last typed.
    url (str): typed URL or hostname.
  """

  DATA_TYPE = 'opera:history:typed_entry'

  def __init__(self):
    """Initializes event data."""
    super(OperaTypedHistoryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.entry_selection = None
    self.entry_type = None
    self.last_typed_time = None
    self.url = None


class OperaTypedHistoryParser(interface.FileObjectParser):
  """Parses the Opera typed_history.xml file."""

  NAME = 'opera_typed_history'
  DATA_FORMAT = 'Opera typed history (typed_history.xml) file'

  _HEADER_READ_SIZE = 128

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Opera typed history file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    data = file_object.read(self._HEADER_READ_SIZE)
    if not data.startswith(b'<?xml'):
      raise errors.WrongParser(
          'Not an Opera typed history file [not a XML]')

    _, _, data = data.partition(b'\n')
    if not data.startswith(b'<typed_history'):
      raise errors.WrongParser(
          'Not an Opera typed history file [wrong XML root key]')

    # For ElementTree to work we need to work on a file object seeked
    # to the beginning.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)

    for history_item in xml.iterfind('typed_history_item'):
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

      event_data = OperaTypedHistoryEventData()
      event_data.entry_type = history_item.get('type', None)
      event_data.last_typed_time = date_time
      event_data.url = history_item.get('content', None)

      if event_data.entry_type == 'selected':
        event_data.entry_selection = 'Filled from autocomplete.'
      elif event_data.entry_type == 'text':
        event_data.entry_selection = 'Manually typed.'

      parser_mediator.ProduceEventData(event_data)


class OperaGlobalHistoryParser(interface.FileObjectParser):
  """Parses the Opera global_history.dat file."""

  NAME = 'opera_global'
  DATA_FORMAT = 'Opera global history (global_history.dat) file'

  _ENCODING = 'utf-8'

  _MAXIMUM_LINE_SIZE = 512

  _SUPPORTED_URL_SCHEMES = frozenset(['file', 'http', 'https', 'ftp'])

  def _IsValidUrl(self, url):
    """Checks if a URL is considered valid.

    Returns:
      bool: True if the URL is valid.
    """
    parsed_url = urlparse.urlparse(url)
    return parsed_url.scheme in self._SUPPORTED_URL_SCHEMES

  def _ParseRecord(self, parser_mediator, text_file_object):
    """Parses an Opera global history record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
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

    title = title.strip()

    timestamp = timestamp.strip()
    try:
      timestamp = int(timestamp, 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unable to convert timestamp: {0:s}'.format(timestamp))
      timestamp = None

    popularity_index = popularity_index.strip()
    try:
      popularity_index = int(popularity_index, 10)
    except ValueError:
      parser_mediator.ProduceExtractionWarning(
          'unable to convert popularity index: {0:s}'.format(popularity_index))
      popularity_index = None

    event_data = OperaGlobalHistoryEventData()
    event_data.popularity_index = popularity_index
    event_data.url = url.strip()

    if timestamp:
      event_data.last_visited_time = dfdatetime_posix_time.PosixTime(
          timestamp=timestamp)

    if title != event_data.url:
      event_data.title = title

    if event_data.popularity_index < 0:
      event_data.description = 'First and Only Visit'
    else:
      event_data.description = 'Last Visit'

    parser_mediator.ProduceEventData(event_data)

    return True

  def _ParseAndValidateRecord(self, parser_mediator, text_file_object):
    """Parses and validates an Opera global history record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
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

    if not self._IsValidUrl(url):
      return False

    try:
      timestamp = int(timestamp, 10)
    except (TypeError, ValueError):
      return False

    try:
      popularity_index = int(popularity_index, 10)
    except (TypeError, ValueError):
      return False

    event_data = OperaGlobalHistoryEventData()
    event_data.last_visited_time = dfdatetime_posix_time.PosixTime(
        timestamp=timestamp)
    event_data.popularity_index = popularity_index
    event_data.url = url

    if title != url:
      event_data.title = title

    if event_data.popularity_index < 0:
      event_data.description = 'First and Only Visit'
    else:
      event_data.description = 'Last Visit'

    parser_mediator.ProduceEventData(event_data)

    return True

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Opera global history file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    encoding = self._ENCODING
    if not encoding:
      encoding = parser_mediator.GetCodePage()

    text_file_object = text_file.TextFile(file_object, encoding=encoding)
    if not self._ParseAndValidateRecord(parser_mediator, text_file_object):
      raise errors.WrongParser('Unable to parse as Opera global_history.dat.')

    while self._ParseRecord(parser_mediator, text_file_object):
      pass


manager.ParsersManager.RegisterParsers([
    OperaTypedHistoryParser, OperaGlobalHistoryParser])
