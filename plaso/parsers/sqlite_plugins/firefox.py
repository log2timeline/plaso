# -*- coding: utf-8 -*-
"""This file contains a parser for the Mozilla Firefox history."""

import sqlite3

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


# Check SQlite version, bail out early if too old.
if sqlite3.sqlite_version_info < (3, 7, 8):
  raise ImportWarning(
      u'FirefoxHistoryParser requires at least SQLite version 3.7.8.')


class FirefoxPlacesBookmarkAnnotation(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark annotation event."""

  DATA_TYPE = u'firefox:places:bookmark_annotation'

  def __init__(
      self, timestamp, timestamp_description, row_id, title, url, content):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      content: The content of the annotation.
    """
    super(FirefoxPlacesBookmarkAnnotation, self).__init__(
        timestamp, timestamp_description)
    self.content = content
    self.offset = row_id
    self.title = title
    self.url = url


class FirefoxPlacesBookmarkFolder(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark folder event."""

  DATA_TYPE = u'firefox:places:bookmark_folder'

  def __init__(self, timestamp, timestamp_description, row_id, title):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
    """
    super(FirefoxPlacesBookmarkFolder, self).__init__(
        timestamp, timestamp_description)
    self.offset = row_id
    self.title = title


class FirefoxPlacesBookmark(time_events.TimestampEvent):
  """Convenience class for a Firefox bookmark event."""

  DATA_TYPE = u'firefox:places:bookmark'

  # TODO: move to formatter.
  _TYPES = {
      1: u'URL',
      2: u'Folder',
      3: u'Separator',
  }
  _TYPES.setdefault(u'N/A')

  def __init__(
      self, timestamp, timestamp_description, row_id, bookmark_type, title,
      url, places_title, hostname, visit_count):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
      row_id: The identifier of the corresponding row.
      bookmark_type: Integer value containing the bookmark type.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      places_title: The places title.
      hostname: The hostname.
      visit_count: The visit count.
    """
    super(FirefoxPlacesBookmark, self).__init__(
        timestamp, timestamp_description)
    self.host = hostname
    self.offset = row_id
    self.places_title = places_title
    self.title = title
    self.type = self._TYPES[bookmark_type]
    self.url = url
    self.visit_count = visit_count


class FirefoxPlacesPageVisitedEvent(time_events.TimestampEvent):
  """Convenience class for a Firefox page visited event."""

  DATA_TYPE = u'firefox:places:page_visited'

  def __init__(self, timestamp, row_id, url, title, hostname, visit_count,
               visit_type, extra):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      url: The URL of the visited page.
      title: The title of the visited page.
      hostname: The visited hostname.
      visit_count: The visit count.
      visit_type: The transition type for the event.
      extra: A list containing extra event data (TODO refactor).
    """
    super(FirefoxPlacesPageVisitedEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.PAGE_VISITED)

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

  DATA_TYPE = u'firefox:downloads:download'

  def __init__(
      self, timestamp, timestamp_description, row_id, name, url, referrer,
      full_path, temporary_location, received_bytes, total_bytes, mime_type):
    """Initializes the event object.

    Args:
      timestamp: The timestamp which is an integer containing the number
                 of micro seconds since January 1, 1970, 00:00:00 UTC.
      timestamp_description: The usage string for the timestamp value.
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
    super(FirefoxDownload, self).__init__(timestamp, timestamp_description)
    self.full_path = full_path
    self.mime_type = mime_type
    self.name = name
    self.offset = row_id
    self.received_bytes = received_bytes
    self.referrer = referrer
    self.temporary_location = temporary_location
    self.total_bytes = total_bytes
    self.url = url


class FirefoxHistoryPlugin(interface.SQLitePlugin):
  """Parses a Firefox history file.

     The Firefox history is stored in a SQLite database file named
     places.sqlite.
  """

  NAME = u'firefox_history'
  DESCRIPTION = u'Parser for Firefox history SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT moz_historyvisits.id, moz_places.url, moz_places.title, '
        u'moz_places.visit_count, moz_historyvisits.visit_date, '
        u'moz_historyvisits.from_visit, moz_places.rev_host, '
        u'moz_places.hidden, moz_places.typed, moz_historyvisits.visit_type '
        u'FROM moz_places, moz_historyvisits '
        u'WHERE moz_places.id = moz_historyvisits.place_id'),
       u'ParsePageVisitedRow'),
      ((u'SELECT moz_bookmarks.type, moz_bookmarks.title AS bookmark_title, '
        u'moz_bookmarks.dateAdded, moz_bookmarks.lastModified, '
        u'moz_places.url, moz_places.title AS places_title, '
        u'moz_places.rev_host, moz_places.visit_count, moz_bookmarks.id '
        u'FROM moz_places, moz_bookmarks '
        u'WHERE moz_bookmarks.fk = moz_places.id AND moz_bookmarks.type <> 3'),
       u'ParseBookmarkRow'),
      ((u'SELECT moz_items_annos.content, moz_items_annos.dateAdded, '
        u'moz_items_annos.lastModified, moz_bookmarks.title, '
        u'moz_places.url, moz_places.rev_host, moz_items_annos.id '
        u'FROM moz_items_annos, moz_bookmarks, moz_places '
        u'WHERE moz_items_annos.item_id = moz_bookmarks.id '
        u'AND moz_bookmarks.fk = moz_places.id'),
       u'ParseBookmarkAnnotationRow'),
      ((u'SELECT moz_bookmarks.id, moz_bookmarks.title,'
        u'moz_bookmarks.dateAdded, moz_bookmarks.lastModified '
        u'FROM moz_bookmarks WHERE moz_bookmarks.type = 2'),
       u'ParseBookmarkFolderRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'moz_places', u'moz_historyvisits', u'moz_bookmarks',
      u'moz_items_annos'])

  # Cache queries.
  URL_CACHE_QUERY = (
      u'SELECT h.id AS id, p.url, p.rev_host FROM moz_places p, '
      u'moz_historyvisits h WHERE p.id = h.place_id')

  def ParseBookmarkAnnotationRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a bookmark annotation row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    if row['dateAdded']:
      event_object = FirefoxPlacesBookmarkAnnotation(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], row['title'], row['url'], row['content'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmarkAnnotation(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], row['title'], row['url'], row['content'])
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseBookmarkFolderRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a bookmark folder row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    if not row['title']:
      title = u'N/A'
    else:
      title = row['title']

    if row['dateAdded']:
      event_object = FirefoxPlacesBookmarkFolder(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], title)
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmarkFolder(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], title)
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseBookmarkRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a bookmark row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    if row['dateAdded']:
      event_object = FirefoxPlacesBookmark(
          row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
          row['id'], row['type'], row['bookmark_title'], row['url'],
          row['places_title'], getattr(row, u'rev_host', u'N/A'),
          row['visit_count'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastModified']:
      event_object = FirefoxPlacesBookmark(
          row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
          row['id'], row['type'], row['bookmark_title'], row['url'],
          row['places_title'], getattr(row, u'rev_host', u'N/A'),
          row['visit_count'])
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParsePageVisitedRow(
      self, parser_mediator, row, query=None, cache=None, database=None,
      **unused_kwargs):
    """Parses a page visited row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
      cache: A cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    # TODO: make extra conditional formatting.
    extras = []
    if row['from_visit']:
      extras.append(u'visited from: {0}'.format(
          self._GetUrl(row['from_visit'], cache, database)))

    if row['hidden'] == u'1':
      extras.append(u'(url hidden)')

    if row['typed'] == u'1':
      extras.append(u'(directly typed)')
    else:
      extras.append(u'(URL not typed directly)')

    if row['visit_date']:
      event_object = FirefoxPlacesPageVisitedEvent(
          row['visit_date'], row['id'], row['url'], row['title'],
          self._ReverseHostname(row['rev_host']), row['visit_count'],
          row['visit_type'], extras)
      parser_mediator.ProduceEvent(event_object, query=query)

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
      return u''

    if len(hostname) > 1:
      if hostname[-1] == '.':
        return hostname[::-1][1:]
      else:
        return hostname[::-1][0:]
    return hostname

  def _GetUrl(self, url_id, cache, database):
    """Return an URL from a reference to an entry in the from_visit table."""
    url_cache_results = cache.GetResults(u'url')
    if not url_cache_results:
      cursor = database.cursor
      result_set = cursor.execute(self.URL_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          result_set, 'url', 'id', ('url', 'rev_host'))
      url_cache_results = cache.GetResults(u'url')

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

  NAME = u'firefox_downloads'
  DESCRIPTION = u'Parser for Firefox downloads SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT moz_downloads.id, moz_downloads.name, moz_downloads.source, '
        u'moz_downloads.target, moz_downloads.tempPath, '
        u'moz_downloads.startTime, moz_downloads.endTime, moz_downloads.state, '
        u'moz_downloads.referrer, moz_downloads.currBytes, '
        u'moz_downloads.maxBytes, moz_downloads.mimeType '
        u'FROM moz_downloads'),
       u'ParseDownloadsRow')]

  # The required tables.
  REQUIRED_TABLES = frozenset([u'moz_downloads'])

  def ParseDownloadsRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a downloads row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    if row['startTime']:
      event_object = FirefoxDownload(
          row['startTime'], eventdata.EventTimestamp.START_TIME, row['id'],
          row['name'], row['source'], row['referrer'], row['target'],
          row['tempPath'], row['currBytes'], row['maxBytes'],
          row['mimeType'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['endTime']:
      event_object = FirefoxDownload(
          row['endTime'], eventdata.EventTimestamp.END_TIME, row['id'],
          row['name'], row['source'], row['referrer'], row['target'],
          row['tempPath'], row['currBytes'], row['maxBytes'],
          row['mimeType'])
      parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugins([
    FirefoxHistoryPlugin, FirefoxDownloadsPlugin])
