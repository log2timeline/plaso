# -*- coding: utf-8 -*-
"""Parser for the Google Chrome History files.

The Chrome History is stored in SQLite database files named History
and Archived History. Where the Archived History does not contain
the downloads table.
"""

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeHistoryFileDownloadedEventData(events.EventData):
  """Chrome History file downloaded event data.

  Attributes:
    full_path (str): full path where the file was downloaded to.
    received_bytes (int): number of bytes received while downloading.
    total_bytes (int): total number of bytes to download.
    url (str): URL of the downloaded file.
  """

  DATA_TYPE = u'chrome:history:file_downloaded'

  def __init__(self):
    """Initializes event data."""
    super(ChromeHistoryFileDownloadedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.full_path = None
    self.received_bytes = None
    self.total_bytes = None
    self.url = None


class ChromeHistoryPageVisitedEventData(events.EventData):
  """Chrome History page visited event data.

  Attributes:
    extra (str): extra event data.
    from_visit (str): URL where the visit originated from.
    hostname (str): visited hostname.
    title (str): title of the visited page.
    typed_count (int): number of characters of the URL that were typed.
    url (str): URL of the visited page.
    visit_source (str): source of the page visit.
  """

  DATA_TYPE = u'chrome:history:page_visited'

  def __init__(self):
    """Initializes event data."""
    super(ChromeHistoryPageVisitedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.extra = None
    self.from_visit = None
    self.host = None
    self.title = None
    self.typed_count = None
    self.url = None
    self.visit_source = None


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

  SCHEMAS = [{
      u'downloads': (
          u'CREATE TABLE downloads (id INTEGER PRIMARY KEY, full_path '
          u'LONGVARCHAR NOT NULL, url LONGVARCHAR NOT NULL, start_time INTEGER '
          u'NOT NULL, received_bytes INTEGER NOT NULL, total_bytes INTEGER NOT '
          u'NULL, state INTEGER NOT NULL)'),
      u'keyword_search_terms': (
          u'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT NULL, '
          u'url_id INTEGER NOT NULL, lower_term LONGVARCHAR NOT NULL, term '
          u'LONGVARCHAR NOT NULL)'),
      u'meta': (
          u'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          u'value LONGVARCHAR)'),
      u'presentation': (
          u'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY, pres_index '
          u'INTEGER NOT NULL)'),
      u'segment_usage': (
          u'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY, segment_id '
          u'INTEGER NOT NULL, time_slot INTEGER NOT NULL, visit_count INTEGER '
          u'DEFAULT 0 NOT NULL)'),
      u'segments': (
          u'CREATE TABLE segments (id INTEGER PRIMARY KEY, name VARCHAR, '
          u'url_id INTEGER NON NULL, pres_index INTEGER DEFAULT -1 NOT NULL)'),
      u'urls': (
          u'CREATE TABLE urls(id INTEGER PRIMARY KEY, url LONGVARCHAR, title '
          u'LONGVARCHAR, visit_count INTEGER DEFAULT 0 NOT NULL, typed_count '
          u'INTEGER DEFAULT 0 NOT NULL, last_visit_time INTEGER NOT NULL, '
          u'hidden INTEGER DEFAULT 0 NOT NULL, favicon_id INTEGER DEFAULT 0 '
          u'NOT NULL)'),
      u'visit_source': (
          u'CREATE TABLE visit_source(id INTEGER PRIMARY KEY, source INTEGER '
          u'NOT NULL)'),
      u'visits': (
          u'CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER NOT NULL, '
          u'visit_time INTEGER NOT NULL, from_visit INTEGER, transition '
          u'INTEGER DEFAULT 0 NOT NULL, segment_id INTEGER, is_indexed '
          u'BOOLEAN)')}]

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

  def _GetHostname(self, url):
    """Retrieves the hostname from a full URL.

    Args:
      url (str): full URL.

    Returns:
      str: hostname or full URL if not hostname could be retrieved.
    """
    if url.startswith(u'http') or url.startswith(u'ftp'):
      _, _, uri = url.partition(u'//')
      hostname, _, _ = uri.partition(u'/')
      return hostname

    if url.startswith(u'about') or url.startswith(u'chrome'):
      hostname, _, _ = url.partition(u'/')
      return hostname

    return url

  def _GetUrl(self, url, cache, database):
    """Retrieves an URL from a reference to an entry in the from_visit table.

    Args:
      url (str): URL.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.
    """
    if not url:
      return u''

    url_cache_results = cache.GetResults(u'url')
    if not url_cache_results:
      result_set = database.Query(self.URL_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(result_set, 'url', 'id', ('url', 'title'))
      url_cache_results = cache.GetResults(u'url')

    reference_url, reference_title = url_cache_results.get(url, [u'', u''])

    if not reference_url:
      return u''

    return u'{0:s} ({1:s})'.format(reference_url, reference_title)

  def _GetVisitSource(self, visit_id, cache, database):
    """Return a string denoting the visit source type if possible.

    Args:
      visit_id (str): ID from the visits table for the particular record.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      str: visit source or None if not found.
    """
    if not visit_id:
      return

    sync_cache_results = cache.GetResults(u'sync')
    if not sync_cache_results:
      result_set = database.Query(self.SYNC_CACHE_QUERY)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(result_set, 'sync', 'id', ('source',))
      sync_cache_results = cache.GetResults(u'sync')

    results = sync_cache_results.get(visit_id, None)
    if results is None:
      return

    return self.VISIT_SOURCE.get(results, None)

  def ParseFileDownloadedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = ChromeHistoryFileDownloadedEventData()
    event_data.full_path = row['full_path']
    event_data.offset = row['id']
    event_data.query = query
    event_data.received_bytes = row['received_bytes']
    event_data.total_bytes = row['total_bytes']
    event_data.url = row['url']

    timestamp = row['start_time']
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseNewFileDownloadedRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = ChromeHistoryFileDownloadedEventData()
    event_data.full_path = row['target_path']
    event_data.offset = row['id']
    event_data.query = query
    event_data.received_bytes = row['received_bytes']
    event_data.total_bytes = row['total_bytes']
    event_data.url = row['url']

    timestamp = row['start_time']
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseLastVisitedRow(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parses a last visited row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
      query (Optional[str]): query.
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
    event_data = ChromeHistoryPageVisitedEventData()
    event_data.extra = u' '.join(extras)
    event_data.from_visit = self._GetUrl(row['from_visit'], cache, database)
    event_data.host = self._GetHostname(row['url'])
    event_data.offset = row['id']
    event_data.query = query
    event_data.title = row['title']
    event_data.typed_count = row['typed_count']
    event_data.url = row['url']
    event_data.visit_source = visit_source

    timestamp = row['visit_time']
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeHistoryPlugin)
