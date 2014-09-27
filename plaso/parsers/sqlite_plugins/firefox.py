#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains a parser for the Mozilla Firefox history."""

import sqlite3

from plaso.events import time_events
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


# Check SQlite version, bail out early if too old.
if sqlite3.sqlite_version_info < (3, 7, 8):
  raise ImportWarning(
      'FirefoxHistoryParser requires at least SQLite version 3.7.8.')


class FirefoxPlacesBookmarkAnnotation(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark annotation event."""

  DATA_TYPE = 'firefox:places:bookmark_annotation'

  def __init__(self, timestamp, usage, row_id, title, url, content):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      usage: Timestamp description string.
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      content: The content of the annotation.
    """
    super(FirefoxPlacesBookmarkAnnotation, self).__init__(
        timestamp, usage)

    self.offset = row_id
    self.title = title
    self.url = url
    self.content = content


class FirefoxPlacesBookmarkFolder(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark folder event."""

  DATA_TYPE = 'firefox:places:bookmark_folder'

  def __init__(self, timestamp, usage, row_id, title):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      usage: Timestamp description string.
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
    """
    super(FirefoxPlacesBookmarkFolder, self).__init__(
        timestamp, usage)

    self.offset = row_id
    self.title = title


class FirefoxPlacesBookmark(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark event."""

  DATA_TYPE = 'firefox:places:bookmark'

  # TODO: move to formatter.
  _TYPES = {
      1: 'URL',
      2: 'Folder',
      3: 'Separator',
  }
  _TYPES.setdefault('N/A')

  # pylint: disable=redefined-builtin
  def __init__(self, timestamp, usage, row_id, type, title, url, places_title,
               hostname, visit_count):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      usage: Timestamp description string.
      row_id: The identifier of the corresponding row.
      type: Integer value containing the bookmark type.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      places_title: The places title.
      hostname: The hostname.
      visit_count: The visit count.
    """
    super(FirefoxPlacesBookmark, self).__init__(timestamp, usage)

    self.offset = row_id
    self.type = self._TYPES[type]
    self.title = title
    self.url = url
    self.places_title = places_title
    self.host = hostname
    self.visit_count = visit_count


class FirefoxPlacesPageVisitedEvent(event.EventObject):
  """Convenience class for a Firefox page visited event."""

  DATA_TYPE = 'firefox:places:page_visited'

  def __init__(self, timestamp, row_id, url, title, hostname, visit_count,
               visit_type, extra):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      url: The URL of the visited page.
      title: The title of the visited page.
      hostname: The visited hostname.
      visit_count: The visit count.
      visit_type: The transition type for the event.
      extra: A list containing extra event data (TODO refactor).
    """
    super(FirefoxPlacesPageVisitedEvent, self).__init__()

    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.PAGE_VISITED

    self.offset = row_id
    self.url = url
    self.title = title
    self.host = hostname
    self.visit_count = visit_count
    self.visit_type = visit_type
    if extra:
      self.extra = extra


class FirefoxDownload(time_events.TimestampEvent):
  """Convenience class for a Firefox download event."""

  DATA_TYPE = 'firefox:downloads:download'

  def __init__(self, timestamp, usage, row_id, name, url, referrer, full_path,
               temporary_location, received_bytes, total_bytes, mime_type):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      usage: Timestamp description string.
      row_id: The identifier of the corresponding row.
      name: The name of the download.
      url: The source URL of the download.
      referrer: The referrer URL of the download.
      full_path: The full path of the target of the download.
      temporary_location: The temporary location of the download.
      received_bytes: The number of bytes received.
      total_bytes: The total number of bytes of the download.
      mime_type: The mime type of the download.
    """
    super(FirefoxDownload, self).__init__(timestamp, usage)

    self.offset = row_id
    self.name = name
    self.url = url
    self.referrer = referrer
    self.full_path = full_path
    self.temporary_location = temporary_location
    self.received_bytes = received_bytes
    self.total_bytes = total_bytes
    self.mime_type = mime_type


class FirefoxHistoryPlugin(interface.SQLitePlugin):
  """Parses a Firefox history file.

     The Firefox history is stored in a SQLite database file named
     places.sqlite.
  """

  NAME = 'firefox_history'
  DESCRIPTION = u'Parser for Firefox history SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT moz_historyvisits.id, moz_places.url, moz_places.title, '
        'moz_places.visit_count, moz_historyvisits.visit_date, '
        'moz_historyvisits.from_visit, moz_places.rev_host, '
        'moz_places.hidden, moz_places.typed, moz_historyvisits.visit_type '
        'FROM moz_places, moz_historyvisits '
        'WHERE moz_places.id = moz_historyvisits.place_id'),
       'ParsePageVisitedRow'),
      (('SELECT moz_bookmarks.type, moz_bookmarks.title AS bookmark_title, '
        'moz_bookmarks.dateAdded, moz_bookmarks.lastModified, '
        'moz_places.url, moz_places.title AS places_title, '
        'moz_places.rev_host, moz_places.visit_count, moz_bookmarks.id '
        'FROM moz_places, moz_bookmarks WHERE moz_bookmarks.fk = moz_places.id '
        'AND moz_bookmarks.type <> 3'),
       'ParseBookmarkRow'),
      (('SELECT moz_items_annos.content, moz_items_annos.dateAdded, '
        'moz_items_annos.lastModified, moz_bookmarks.title, '
        'moz_places.url, moz_places.rev_host, moz_items_annos.id '
        'FROM moz_items_annos, moz_bookmarks, moz_places '
        'WHERE moz_items_annos.item_id = moz_bookmarks.id '
        'AND moz_bookmarks.fk = moz_places.id'),
       'ParseBookmarkAnnotationRow'),
      (('SELECT moz_bookmarks.id, moz_bookmarks.title,'
        'moz_bookmarks.dateAdded, moz_bookmarks.lastModified '
        'FROM moz_bookmarks WHERE moz_bookmarks.type = 2'),
       'ParseBookmarkFolderRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      'moz_places', 'moz_historyvisits', 'moz_bookmarks', 'moz_items_annos'])

  # Cache queries.
  URL_CACHE_QUERY = (
      'SELECT h.id AS id, p.url, p.rev_host FROM moz_places p, '
      'moz_historyvisits h WHERE p.id = h.place_id')

  def ParseBookmarkAnnotationRow(
      self, parser_context, row, query=None, **unused_kwargs):
    """Parses a bookmark annotation row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    if row['dateAdded']:
      event_object = FirefoxPlacesBookmarkAnnotation(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], row['title'], row['url'], row['content'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmarkAnnotation(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], row['title'], row['url'], row['content'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

  def ParseBookmarkFolderRow(
      self, parser_context, row, query=None, **unused_kwargs):
    """Parses a bookmark folder row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    if not row['title']:
      title = 'N/A'
    else:
      title = row['title']

    if row['dateAdded']:
      event_object = FirefoxPlacesBookmarkFolder(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], title)
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmarkFolder(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], title)
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

  def ParseBookmarkRow(self, parser_context, row, query=None, **unused_kwargs):
    """Parses a bookmark row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    if row['dateAdded']:
      event_object = FirefoxPlacesBookmark(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], row['type'], row['bookmark_title'], row['url'],
          row['places_title'], getattr(row, 'rev_host', 'N/A'),
          row['visit_count'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmark(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], row['type'], row['bookmark_title'], row['url'],
          row['places_title'], getattr(row, 'rev_host', 'N/A'),
          row['visit_count'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

  def ParsePageVisitedRow(
      self, parser_context, row, query=None, cache=None, database=None,
      **unused_kwargs):
    """Parses a page visited row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
      cache: A cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).
    """
    # TODO: make extra conditional formatting.
    extras = []
    if row['from_visit']:
      extras.append(u'visited from: {0}'.format(
          self._GetUrl(row['from_visit'], cache, database)))

    if row['hidden'] == '1':
      extras.append('(url hidden)')

    if row['typed'] == '1':
      extras.append('(directly typed)')
    else:
      extras.append('(URL not typed directly)')

    if row['visit_date']:
      event_object = FirefoxPlacesPageVisitedEvent(
          row['visit_date'], row['id'], row['url'], row['title'],
          self._ReverseHostname(row['rev_host']), row['visit_count'],
          row['visit_type'], extras)
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

  def _ReverseHostname(self, hostname):
    """Reverses the hostname and strips the leading dot.

    The hostname entry is reversed:
      moc.elgoog.www.
    Should be:
      www.google.com

    Args:
      hostname: The reversed hostname.

    Returns:
      Reversed string without a leading dot.
    """
    if not hostname:
      return ''

    if len(hostname) > 1:
      if hostname[-1] == '.':
        return hostname[::-1][1:]
      else:
        return hostname[::-1][0:]
    return hostname

  def _GetUrl(self, url_id, cache, database):
    """Return an URL from a reference to an entry in the from_visit table."""
    url_cache_results = cache.GetResults('url')
    if not url_cache_results:
      cursor = database.cursor
      result_set = cursor.execute(self.URL_CACHE_QUERY)
      cache.CacheQueryResults(
          result_set, 'url', 'id', ('url', 'rev_host'))
      url_cache_results = cache.GetResults('url')

    url, reverse_host = url_cache_results.get(url_id, [u'', u''])

    if not url:
      return u''

    hostname = self._ReverseHostname(reverse_host)
    return u'{:s} ({:s})'.format(url, hostname)


class FirefoxDownloadsPlugin(interface.SQLitePlugin):
  """Parses a Firefox downloads file.

     The Firefox downloads history is stored in a SQLite database file named
     downloads.sqlite.
  """

  NAME = 'firefox_downloads'
  DESCRIPTION = u'Parser for Firefox downloads SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT moz_downloads.id, moz_downloads.name, moz_downloads.source, '
        'moz_downloads.target, moz_downloads.tempPath, '
        'moz_downloads.startTime, moz_downloads.endTime, moz_downloads.state, '
        'moz_downloads.referrer, moz_downloads.currBytes, '
        'moz_downloads.maxBytes, moz_downloads.mimeType '
        'FROM moz_downloads'),
       'ParseDownloadsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset(['moz_downloads'])

  def ParseDownloadsRow(self, parser_context, row, query=None, **unused_kwargs):
    """Parses a downloads row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    if row['startTime']:
      event_object = FirefoxDownload(
          row['startTime'], eventdata.EventTimestamp.START_TIME,
          row['id'], row['name'], row['source'], row['referrer'], row['target'],
          row['tempPath'], row['currBytes'], row['maxBytes'], row['mimeType'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)

    if row['endTime']:
      event_object = FirefoxDownload(
          row['endTime'], eventdata.EventTimestamp.END_TIME,
          row['id'], row['name'], row['source'], row['referrer'], row['target'],
          row['tempPath'], row['currBytes'], row['maxBytes'], row['mimeType'])
      parser_context.ProduceEvent(
          event_object, plugin_name=self.NAME, query=query)


sqlite.SQLiteParser.RegisterPlugin(FirefoxHistoryPlugin)
sqlite.SQLiteParser.RegisterPlugin(FirefoxDownloadsPlugin)
