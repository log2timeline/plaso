# -*- coding: utf-8 -*-
"""Parser for the Google Chrome History files.

   The Chrome History is stored in SQLite database files named History
   and Archived History. Where the Archived History does not contain
   the downloads table.
"""

from plaso.events import time_events
from plaso.lib import timelib
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeHistoryFileDownloadedEvent(time_events.TimestampEvent):
  """Convenience class for a Chrome History file downloaded event."""
  DATA_TYPE = u'chrome:history:file_downloaded'

  def __init__(
      self, timestamp, row_id, url, full_path, received_bytes, total_bytes):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      row_id: The identifier of the corresponding row.
      url: The URL of the downloaded file.
      full_path: The full path where the file was downloaded to.
      received_bytes: The number of bytes received while downloading.
      total_bytes: The total number of bytes to download.
    """
    super(ChromeHistoryFileDownloadedEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.FILE_DOWNLOADED)

    self.offset = row_id
    self.url = url
    self.full_path = full_path
    self.received_bytes = received_bytes
    self.total_bytes = total_bytes


class ChromeHistoryPageVisitedEvent(time_events.WebKitTimeEvent):
  """Convenience class for a Chrome History page visited event."""
  DATA_TYPE = u'chrome:history:page_visited'

  # TODO: refactor extra to be conditional arguments.
  def __init__(
      self, webkit_time, row_id, url, title, hostname, typed_count, from_visit,
      extra, visit_source):
    """Initializes the event object.

    Args:
      webkit_time: The WebKit time value.
      row_id: The identifier of the corresponding row.
      url: The URL of the visited page.
      title: The title of the visited page.
      hostname: The visited hostname.
      typed_count: The number of characters of the URL that were typed.
      from_visit: The URL where the visit originated from.
      extra: String containing extra event data.
      visit_source: The source of the page visit, if defined.
    """
    super(ChromeHistoryPageVisitedEvent, self).__init__(
        webkit_time, eventdata.EventTimestamp.PAGE_VISITED)

    self.offset = row_id
    self.url = url
    self.title = title
    self.host = hostname
    self.typed_count = typed_count
    self.from_visit = from_visit
    self.extra = extra
    if visit_source is not None:
      self.visit_source = visit_source


class ChromeHistoryPlugin(interface.SQLitePlugin):
  """Parse Chrome Archived History and History files."""

  NAME = u'chrome_history'
  DESCRIPTION = u'Parser for Chrome history SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT urls.id, urls.url, urls.title, urls.visit_count, '
        u'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
        u'visit_time, visits.from_visit, visits.transition, visits.id '
        u'AS visit_id FROM urls, visits WHERE urls.id = visits.url ORDER '
        u'BY visits.visit_time'), u'ParseLastVisitedRow'),
      ((u'SELECT downloads.id AS id, downloads.start_time,'
        u'downloads.target_path, downloads_url_chains.url, '
        u'downloads.received_bytes, downloads.total_bytes FROM downloads,'
        u' downloads_url_chains WHERE downloads.id = '
        u'downloads_url_chains.id'), u'ParseNewFileDownloadedRow'),
      ((u'SELECT id, full_path, url, start_time, received_bytes, '
        u'total_bytes,state FROM downloads'), u'ParseFileDownloadedRow')]

  # The required tables common to Archived History and History.
  REQUIRED_TABLES = frozenset([
      u'keyword_search_terms', u'meta', u'urls', u'visits', u'visit_source'])

  # Queries for cache building.
  URL_CACHE_QUERY = (
      u'SELECT visits.id AS id, urls.url, urls.title FROM '
      u'visits, urls WHERE urls.id = visits.url')
  SYNC_CACHE_QUERY = u'SELECT id, source FROM visit_source'

  # The following definition for values can be found here:
  # http://src.chromium.org/svn/trunk/src/content/public/common/ \
  # page_transition_types_list.h
  PAGE_TRANSITION = {
      0: u'LINK',
      1: u'TYPED',
      2: u'AUTO_BOOKMARK',
      3: u'AUTO_SUBFRAME',
      4: u'MANUAL_SUBFRAME',
      5: u'GENERATED',
      6: u'START_PAGE',
      7: u'FORM_SUBMIT',
      8: u'RELOAD',
      9: u'KEYWORD',
      10: u'KEYWORD_GENERATED '
  }

  TRANSITION_LONGER = {
      0: u'User clicked a link',
      1: u'User typed the URL in the URL bar',
      2: u'Got through a suggestion in the UI',
      3: (u'Content automatically loaded in a non-toplevel frame - user may '
          u'not realize'),
      4: u'Subframe explicitly requested by the user',
      5: (u'User typed in the URL bar and selected an entry from the list - '
          u'such as a search bar'),
      6: u'The start page of the browser',
      7: u'A form the user has submitted values to',
      8: (u'The user reloaded the page, eg by hitting the reload button or '
          u'restored a session'),
      9: (u'URL what was generated from a replaceable keyword other than the '
          u'default search provider'),
      10: u'Corresponds to a visit generated from a KEYWORD'
  }

  # The following is the values for the source enum found in the visit_source
  # table and describes where a record originated from (if it originates from a
  # different storage than locally generated).
  # The source can be found here:
  # http://src.chromium.org/svn/trunk/src/chrome/browser/history/\
  # history_types.h
  VISIT_SOURCE = {
      0: u'SOURCE_SYNCED',
      1: u'SOURCE_BROWSED',
      2: u'SOURCE_EXTENSION',
      3: u'SOURCE_FIREFOX_IMPORTED',
      4: u'SOURCE_IE_IMPORTED',
      5: u'SOURCE_SAFARI_IMPORTED'
  }

  CORE_MASK = 0xff

  def _GetHostname(self, hostname):
    """Return a hostname from a full URL."""
    if hostname.startswith(u'http') or hostname.startswith(u'ftp'):
      _, _, uri = hostname.partition(u'//')
      hostname, _, _ = uri.partition(u'/')

      return hostname

    if hostname.startswith(u'about') or hostname.startswith(u'chrome'):
      site, _, _ = hostname.partition(u'/')
      return site

    return hostname

  def _GetUrl(self, url, cache, database):
    """Return an URL from a reference to an entry in the from_visit table."""
    if not url:
      return u''

    url_cache_results = cache.GetResults(u'url')
    if not url_cache_results:
      result_set = database.Query(self.URL_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          result_set, 'url', 'id', ('url', 'title'))
      url_cache_results = cache.GetResults(u'url')

    reference_url, reference_title = url_cache_results.get(url, [u'', u''])

    if not reference_url:
      return u''

    return u'{0:s} ({1:s})'.format(reference_url, reference_title)

  def _GetVisitSource(self, visit_id, cache, database):
    """Return a string denoting the visit source type if possible.

    Args:
      visit_id: The ID from the visits table for the particular record.
      cache: A cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).

    Returns:
      A string with the visit source, None if not found.
    """
    if not visit_id:
      return

    sync_cache_results = cache.GetResults(u'sync')
    if not sync_cache_results:
      result_set = database.Query(self.SYNC_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          result_set, 'sync', 'id', ('source',))
      sync_cache_results = cache.GetResults(u'sync')

    results = sync_cache_results.get(visit_id, None)
    if results is None:
      return

    return self.VISIT_SOURCE.get(results, None)

  def ParseFileDownloadedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    timestamp = timelib.Timestamp.FromPosixTime(row['start_time'])
    event_object = ChromeHistoryFileDownloadedEvent(
        timestamp, row['id'], row['url'], row['full_path'],
        row['received_bytes'], row['total_bytes'])
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseNewFileDownloadedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    timestamp = timelib.Timestamp.FromWebKitTime(row['start_time'])
    event_object = ChromeHistoryFileDownloadedEvent(
        timestamp, row['id'], row['url'], row['target_path'],
        row['received_bytes'], row['total_bytes'])
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseLastVisitedRow(
      self, parser_mediator, row, query=None, cache=None, database=None,
      **unused_kwargs):
    """Parses a last visited row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
      cache: Optional cache object (instance of SQLiteCache).
             The default is None.
      database: Optional database object (instance of SQLiteDatabase).
                The default is None.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    extras = []

    transition_nr = row['transition'] & self.CORE_MASK
    page_transition = self.PAGE_TRANSITION.get(transition_nr, u'')
    if page_transition:
      extras.append(u'Type: [{0:s} - {1:s}]'.format(
          page_transition, self.TRANSITION_LONGER.get(transition_nr, u'')))

    if row['hidden'] == u'1':
      extras.append(u'(url hidden)')

    # TODO: move to formatter.
    count = row['typed_count']
    if count >= 1:
      if count > 1:
        multi = u's'
      else:
        multi = u''

      extras.append(u'(type count {1:d} time{0:s})'.format(multi, count))
    else:
      extras.append(u'(URL not typed directly - no typed count)')

    visit_source = self._GetVisitSource(row['visit_id'], cache, database)

    # TODO: replace extras by conditional formatting.
    event_object = ChromeHistoryPageVisitedEvent(
        row['visit_time'], row['id'], row['url'], row['title'],
        self._GetHostname(row['url']), row['typed_count'],
        self._GetUrl(row['from_visit'], cache, database), u' '.join(extras),
        visit_source)
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(ChromeHistoryPlugin)
