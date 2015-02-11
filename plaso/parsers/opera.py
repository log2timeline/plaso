#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

  DATA_TYPE = 'opera:history:typed_entry'

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

    if entry_type == 'selected':
      self.entry_selection = 'Filled from autocomplete.'
    elif entry_type == 'text':
      self.entry_selection = 'Manually typed.'

    self.timestamp = timelib.Timestamp.FromTimeString(last_typed_time)
    self.timestamp_desc = eventdata.EventTimestamp.LAST_VISITED_TIME


class OperaGlobalHistoryEvent(time_events.PosixTimeEvent):
  """An EventObject for an Opera global history entry."""

  DATA_TYPE = 'opera:history:entry'

  def __init__(self, timestamp, url, title, popularity_index):
    """Initialize the event object."""
    super(OperaGlobalHistoryEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.PAGE_VISITED, self.DATA_TYPE)

    self.url = url
    if title != url:
      self.title = title

    self.popularity_index = popularity_index

    if popularity_index < 0:
      self.description = 'First and Only Visit'
    else:
      self.description = 'Last Visit'


class OperaTypedHistoryParser(interface.BaseParser):
  """Parses the Opera typed_history.xml file."""

  NAME = 'opera_typed_history'
  DESCRIPTION = u'Parser for Opera typed_history.xml files.'

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from an Opera typed history file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    # Need to verify the first line to make sure this is a) XML and
    # b) the right XML.
    first_line = text_file_object.readline(90)

    if not first_line.startswith('<?xml version="1.0'):
      file_object.close()
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [not a XML]')

    # We read in the second line due to the fact that ElementTree
    # reads the entire file in memory to parse the XML string and
    # we only care about the XML file with the correct root key,
    # which denotes a typed_history.xml file.
    second_line = text_file_object.readline(50).strip()

    if second_line != '<typed_history>':
      file_object.close()
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [wrong XML root key]')

    # For ElementTree to work we need to work on a file object seeked
    # to the beginning.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)



    for history_item in xml.iterfind('typed_history_item'):
      content = history_item.get('content', '')
      last_typed = history_item.get('last_typed', '')
      entry_type = history_item.get('type', '')

      event_object = OperaTypedHistoryEvent(last_typed, content, entry_type)
      parser_mediator.ProduceEvent(event_object)

    file_object.close()


class OperaGlobalHistoryParser(interface.BaseParser):
  """Parses the Opera global_history.dat file."""

  NAME = 'opera_global'
  DESCRIPTION = u'Parser for Opera global_history.dat files.'

  _SUPPORTED_URL_SCHEMES = frozenset(['file', 'http', 'https', 'ftp'])

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
      if len(title_raw) == max_line_length and not title_raw.endswith('\n'):
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
      logging.debug(u'Unable to read in timestamp [{!r}]'.format(
          timestamp_line))
      return None, None, None, None

    try:
      popularity_index = int(popularity_line, 10)
    except ValueError:
      try:
        logging.debug(u'Unable to read in popularity index[{}]'.format(
            popularity_line))
      except UnicodeDecodeError:
        logging.debug(
            u'Unable to read in popularity index [unable to print '
            u'bad line]')
      return None, None, None, None

    # Try to get the data into unicode.
    try:
      title_unicode = title.decode('utf-8')
    except UnicodeDecodeError:
      partial_title = title.decode('utf-8', 'ignore')
      title_unicode = u'Warning: partial line, starts with: {}'.format(
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

  def Parse(self, parser_mediator, **kwargs):
    """Extract data from an Opera global history file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
    """
    file_object = parser_mediator.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    text_file_object = text_file.TextFile(file_object)

    try:
      title, url, timestamp, popularity_index = self._ReadRecord(
          text_file_object, 400)
    except errors.NotAText:
      file_object.close()
      raise errors.UnableToParseFile(
          u'Not an Opera history file [not a text file].')

    if not title:
      file_object.close()
      raise errors.UnableToParseFile(
          u'Not an Opera history file [no title present].')

    if not self._IsValidUrl(url):
      file_object.close()
      raise errors.UnableToParseFile(
          u'Not an Opera history file [not a valid URL].')

    if not timestamp:
      file_object.close()
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

    file_object.close()


manager.ParsersManager.RegisterParsers([
    OperaTypedHistoryParser, OperaGlobalHistoryParser])
