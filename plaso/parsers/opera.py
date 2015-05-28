# -*- coding: utf-8 -*-
"""Parsers for Opera Browser history files."""

import logging
import os
import urllib2

from dfvfs.helpers import text_file
from xml.etree import ElementTree

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.lib import utils
from plaso.parsers import interface
from plaso.parsers import manager


class OperaTypedHistoryEvent(event.EventObject):
  """An EventObject for an Opera typed history entry."""

  DATA_TYPE = u'opera:history:typed_entry'

  def __init__(self, last_typed_time, url, entry_type):
    """A constructor for the typed history event.

    Args:
      last_typed_time: A ISO 8601 string denoting the last time
                       the URL was typed into a browser.
      url: The url, or the typed hostname.
      entry_type: A string indicating whether the URL was directly
                  typed in or the result of the user choosing from the
                  auto complete (based on prior history).
    """
    super(OperaTypedHistoryEvent, self).__init__()
    self.url = url
    self.entry_type = entry_type

    if entry_type == u'selected':
      self.entry_selection = u'Filled from autocomplete.'
    elif entry_type == u'text':
      self.entry_selection = u'Manually typed.'

    self.timestamp = timelib.Timestamp.FromTimeString(last_typed_time)
    self.timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME


class OperaGlobalHistoryEvent(time_events.PosixTimeEvent):
  """An EventObject for an Opera global history entry."""

  DATA_TYPE = u'opera:history:entry'

  def __init__(self, timestamp, url, title, popularity_index):
    """Initialize the event object."""
    super(OperaGlobalHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.PAGE_VISITED, self.DATA_TYPE)

    self.url = url
    if title != url:
      self.title = title

    self.popularity_index = popularity_index

    if popularity_index < 0:
      self.description = u'First and Only Visit'
    else:
      self.description = u'Last Visit'


class OperaTypedHistoryParser(interface.SingleFileBaseParser):
  """Parses the Opera typed_history.xml file."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'opera_typed_history'
  DESCRIPTION = u'Parser for Opera typed_history.xml files.'

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an Opera typed history file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    # Need to verify the first line to make sure this is a) XML and
    # b) the right XML.
    first_line = text_file_object.readline(90)

    # Note that we must check the data here as a string first, otherwise
    # forcing first_line to convert to Unicode can raise a UnicodeDecodeError.
    if not first_line.startswith(b'<?xml version="1.0'):
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [not a XML]')

    # We read in the second line due to the fact that ElementTree
    # reads the entire file in memory to parse the XML string and
    # we only care about the XML file with the correct root key,
    # which denotes a typed_history.xml file.
    second_line = text_file_object.readline(50).strip()

    # Note that we must check the data here as a string first, otherwise
    # forcing second_line to convert to Unicode can raise a UnicodeDecodeError.
    if second_line != b'<typed_history>':
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [wrong XML root key]')

    # For ElementTree to work we need to work on a file object seeked
    # to the beginning.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)



    for history_item in xml.iterfind(u'typed_history_item'):
      content = history_item.get(u'content', u'')
      last_typed = history_item.get(u'last_typed', u'')
      entry_type = history_item.get(u'type', u'')

      event_object = OperaTypedHistoryEvent(last_typed, content, entry_type)
      parser_mediator.ProduceEvent(event_object)


class OperaGlobalHistoryParser(interface.SingleFileBaseParser):
  """Parses the Opera global_history.dat file."""

  NAME = u'opera_global'
  DESCRIPTION = u'Parser for Opera global_history.dat files.'

  _SUPPORTED_URL_SCHEMES = frozenset([u'file', u'http', u'https', u'ftp'])

  def _IsValidUrl(self, url):
    """A simple test to see if an URL is considered valid."""
    parsed_url = urllib2.urlparse.urlparse(url)

    # Few supported first URL entries.
    if parsed_url.scheme in self._SUPPORTED_URL_SCHEMES:
      return True

    return False

  def _ReadRecord(self, text_file_object, max_line_length=0):
    """Return a single record from an Opera global_history file.

    A single record consists of four lines, with each line as:
      Title of page (or the URL if not there).
      Website URL.
      Timestamp in POSIX time.
      Popularity index (-1 if first time visited).

    Args:
      text_file_object: A text file object (instance of dfvfs.TextFile).
      max_line_length: An integer that denotes the maximum byte
                       length for each line read.

    Returns:
      A tuple of: title, url, timestamp, popularity_index.

    Raises:
      errors.NotAText: If the file being read is not a text file.
    """
    if max_line_length:
      title_raw = text_file_object.readline(max_line_length)
      if len(title_raw) == max_line_length and not title_raw.endswith(u'\n'):
        return None, None, None, None
      if not utils.IsText(title_raw):
        raise errors.NotAText(u'Title line is not a text.')
      title = title_raw.strip()
    else:
      title = text_file_object.readline().strip()

    if not title:
      return None, None, None, None

    url = text_file_object.readline().strip()

    if not url:
      return None, None, None, None

    timestamp_line = text_file_object.readline().strip()
    popularity_line = text_file_object.readline().strip()

    try:
      timestamp = int(timestamp_line, 10)
    except ValueError:
      if len(timestamp_line) > 30:
        timestamp_line = timestamp_line[0:30]
      logging.debug(u'Unable to read in timestamp [{0!r}]'.format(
          timestamp_line))
      return None, None, None, None

    try:
      popularity_index = int(popularity_line, 10)
    except ValueError:
      try:
        logging.debug(u'Unable to read in popularity index[{0:s}]'.format(
            popularity_line))
      except UnicodeDecodeError:
        logging.debug(
            u'Unable to read in popularity index [unable to print '
            u'bad line]')
      return None, None, None, None

    # Try to get the data into unicode.
    try:
      title_unicode = title.decode(u'utf-8')
    except UnicodeDecodeError:
      partial_title = title.decode(u'utf-8', u'ignore')
      title_unicode = u'Warning: partial line, starts with: {0:s}'.format(
          partial_title)

    return title_unicode, url, timestamp, popularity_index

  def _ReadRecords(self, text_file_object):
    """Yield records read from an Opera global_history file.

    A single record consists of four lines, with each line as:
      Title of page (or the URL if not there).
      Website URL.
      Timestamp in POSIX time.
      Popularity index (-1 if first time visited).

    Args:
      text_file_object: A text file object (instance of dfvfs.TextFile).

    Yields:
      A tuple of: title, url, timestamp, popularity_index.
    """
    while True:
      title, url, timestamp, popularity_index = self._ReadRecord(
          text_file_object)

      if not title:
        raise StopIteration
      if not url:
        raise StopIteration
      if not popularity_index:
        raise StopIteration

      yield title, url, timestamp, popularity_index

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an Opera global history file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    try:
      title, url, timestamp, popularity_index = self._ReadRecord(
          text_file_object, 400)
    except errors.NotAText:
      raise errors.UnableToParseFile(
          u'Not an Opera history file [not a text file].')

    if not title:
      raise errors.UnableToParseFile(
          u'Not an Opera history file [no title present].')

    if not self._IsValidUrl(url):
      raise errors.UnableToParseFile(
          u'Not an Opera history file [not a valid URL].')

    if not timestamp:
      raise errors.UnableToParseFile(
          u'Not an Opera history file [timestamp does not exist].')

    event_object = OperaGlobalHistoryEvent(
        timestamp, url, title, popularity_index)
    parser_mediator.ProduceEvent(event_object)

    # Read in the rest of the history file.
    for title, url, timestamp, popularity_index in self._ReadRecords(
        text_file_object):
      event_object = OperaGlobalHistoryEvent(
          timestamp, url, title, popularity_index)
      parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParsers([
    OperaTypedHistoryParser, OperaGlobalHistoryParser])
