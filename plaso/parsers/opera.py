#!/usr/bin/python
# -*- coding: utf-8 -*-
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
import urllib2

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib
from plaso.lib import utils

from xml.etree import ElementTree


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


class OperaGlobalHistoryEvent(event.PosixTimeEvent):
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


class OperaTypedHistoryParser(parser.BaseParser):
  """Parses the Opera typed_history.xml file."""

  NAME = 'opera_typed_history'

  def Parse(self, file_like_object):
    """Parse the history file and yield extracted events."""

    # Need to verify the first line to make sure this is a) XML and
    # b) the right XML.
    first_line = file_like_object.readline(90)

    if not first_line.startswith('<?xml version="1.0'):
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [not a XML]')

    # We read in the second line due to the fact that ElementTree
    # reads the entire file in memory to parse the XML string and
    # we only care about the XML file with the correct root key,
    # which denotes a typed_history.xml file.
    second_line = file_like_object.readline(50).strip()

    if second_line != '<typed_history>':
      raise errors.UnableToParseFile(
          u'Not an Opera typed history file [wrong XML root key]')

    # For ElementTree to work we need to work on a filehandle seeked
    # to the beginning.
    file_like_object.seek(0)

    xml = ElementTree.parse(file_like_object)

    for history_item in xml.iterfind('typed_history_item'):
      content = history_item.get('content', '')
      last_typed = history_item.get('last_typed', '')
      entry_type = history_item.get('type', '')

      yield OperaTypedHistoryEvent(last_typed, content, entry_type)


class OperaGlobalHistoryParser(parser.BaseParser):
  """Parses the Opera global_history.dat file."""

  NAME = 'opera_global'

  _SUPPORTED_URL_SCHEMES = frozenset(['file', 'http', 'https', 'ftp'])

  def ReadRecord(self, file_like_object, max_line_length=0):
    """Return a single record from an Opera global_history file.

    A single record consists of four lines, with each line as:
      Title of page (or the URL if not there).
      Website URL.
      Timestamp in POSIX time.
      Popularity index (-1 if first time visited).

    Args:
      file_like_object: A file-like object that is used to read
                        the record from.
      max_line_length: An integer that denotes the maximum byte
                       length for each line read.

    Returns:
      A tuple of: title, url, timestamp, popularity_index.

    Raises:
      errors.NotAText: If the file being read is not a text file.
    """
    if max_line_length:
      title_raw = file_like_object.readline(max_line_length)
      if len(title_raw) == max_line_length and not title_raw.endswith('\n'):
        return None, None, None, None
      if not utils.IsText(title_raw):
        raise errors.NotAText(u'Title line is not a text.')
      title = title_raw.strip()
    else:
      title = file_like_object.readline().strip()

    if not title:
      return None, None, None, None

    url = file_like_object.readline().strip()

    if not url:
      return None, None, None, None

    timestamp_line = file_like_object.readline().strip()
    popularity_line = file_like_object.readline().strip()

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

  def ReadRecords(self, file_like_object):
    """Yield records read from an Opera global_history file.

    A single record consists of four lines, with each line as:
      Title of page (or the URL if not there).
      Website URL.
      Timestamp in POSIX time.
      Popularity index (-1 if first time visited).

    Args:
      file_like_object: A file-like object that is used to read
                        the record from.

    Yields:
      A tuple of: title, url, timestamp, popularity_index.
    """
    while 1:
      title, url, timestamp, popularity_index = self.ReadRecord(
          file_like_object)
      if not title:
        raise StopIteration
      if not url:
        raise StopIteration
      if not popularity_index:
        raise StopIteration

      yield title, url, timestamp, popularity_index

  def _IsValidUrl(self, url):
    """A simple test to see if an URL is considered valid."""
    parsed_url = urllib2.urlparse.urlparse(url)

    # Few supported first URL entries.
    if parsed_url.scheme in self._SUPPORTED_URL_SCHEMES:
      return True

    return False

  def Parse(self, file_like_object):
    """Parse the history file and yield extracted events."""
    try:
      title, url, timestamp, popularity_index = self.ReadRecord(
          file_like_object, 400)
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

    yield OperaGlobalHistoryEvent(timestamp, url, title, popularity_index)

    # Read in the rest of the history file.
    for title, url, timestamp, popularity_index in self.ReadRecords(
        file_like_object):
      yield OperaGlobalHistoryEvent(timestamp, url, title, popularity_index)

