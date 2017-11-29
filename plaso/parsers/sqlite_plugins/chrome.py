# -*- coding: utf-8 -*-
"""Parser for the Google Chrome History files.

The Chrome History is stored in SQLite database files named History
and Archived History. Where the Archived History does not contain
the downloads table.
"""

from __future__ import unicode_literals

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

  DATA_TYPE = 'chrome:history:file_downloaded'

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

  DATA_TYPE = 'chrome:history:page_visited'

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

  NAME = 'chrome_history'
  DESCRIPTION = 'Parser for Chrome history SQLite database files.'

  # Define the needed queries.
  QUERIES = [
      (('SELECT urls.id, urls.url, urls.title, urls.visit_count, '
        'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
        'visit_time, visits.from_visit, visits.transition, visits.id '
        'AS visit_id FROM urls, visits WHERE urls.id = visits.url ORDER '
        'BY visits.visit_time'), 'ParseLastVisitedRow'),
      (('SELECT downloads.id AS id, downloads.start_time,'
        'downloads.target_path, downloads_url_chains.url, '
        'downloads.received_bytes, downloads.total_bytes FROM downloads,'
        ' downloads_url_chains WHERE downloads.id = '
        'downloads_url_chains.id'), 'ParseNewFileDownloadedRow'),
      (('SELECT id, full_path, url, start_time, received_bytes, '
        'total_bytes,state FROM downloads'), 'ParseFileDownloadedRow')]

  # The required tables common to Archived History and History.
  REQUIRED_TABLES = frozenset([
      'keyword_search_terms', 'meta', 'urls', 'visits', 'visit_source'])

  SCHEMAS = [{
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY, full_path '
          'LONGVARCHAR NOT NULL, url LONGVARCHAR NOT NULL, start_time INTEGER '
          'NOT NULL, received_bytes INTEGER NOT NULL, total_bytes INTEGER NOT '
          'NULL, state INTEGER NOT NULL)'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT NULL, '
          'url_id INTEGER NOT NULL, lower_term LONGVARCHAR NOT NULL, term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'presentation': (
          'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY, pres_index '
          'INTEGER NOT NULL)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY, segment_id '
          'INTEGER NOT NULL, time_slot INTEGER NOT NULL, visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY, name VARCHAR, '
          'url_id INTEGER NON NULL, pres_index INTEGER DEFAULT -1 NOT NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY, url LONGVARCHAR, title '
          'LONGVARCHAR, visit_count INTEGER DEFAULT 0 NOT NULL, typed_count '
          'INTEGER DEFAULT 0 NOT NULL, last_visit_time INTEGER NOT NULL, '
          'hidden INTEGER DEFAULT 0 NOT NULL, favicon_id INTEGER DEFAULT 0 '
          'NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY, source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY, url INTEGER NOT NULL, '
          'visit_time INTEGER NOT NULL, from_visit INTEGER, transition '
          'INTEGER DEFAULT 0 NOT NULL, segment_id INTEGER, is_indexed '
          'BOOLEAN)')}]

  # Queries for cache building.
  URL_CACHE_QUERY = (
      'SELECT visits.id AS id, urls.url, urls.title FROM '
      'visits, urls WHERE urls.id = visits.url')
  SYNC_CACHE_QUERY = 'SELECT id, source FROM visit_source'

  # The following definition for values can be found here:
  # http://src.chromium.org/svn/trunk/src/content/public/common/ \
  # page_transition_types_list.h
  PAGE_TRANSITION = {
      0: 'LINK',
      1: 'TYPED',
      2: 'AUTO_BOOKMARK',
      3: 'AUTO_SUBFRAME',
      4: 'MANUAL_SUBFRAME',
      5: 'GENERATED',
      6: 'START_PAGE',
      7: 'FORM_SUBMIT',
      8: 'RELOAD',
      9: 'KEYWORD',
      10: 'KEYWORD_GENERATED '
  }

  TRANSITION_LONGER = {
      0: 'User clicked a link',
      1: 'User typed the URL in the URL bar',
      2: 'Got through a suggestion in the UI',
      3: ('Content automatically loaded in a non-toplevel frame - user may '
          'not realize'),
      4: 'Subframe explicitly requested by the user',
      5: ('User typed in the URL bar and selected an entry from the list - '
          'such as a search bar'),
      6: 'The start page of the browser',
      7: 'A form the user has submitted values to',
      8: ('The user reloaded the page, eg by hitting the reload button or '
          'restored a session'),
      9: ('URL what was generated from a replaceable keyword other than the '
          'default search provider'),
      10: 'Corresponds to a visit generated from a KEYWORD'
  }

  # The following is the values for the source enum found in the visit_source
  # table and describes where a record originated from (if it originates from a
  # different storage than locally generated).
  # The source can be found here:
  # http://src.chromium.org/svn/trunk/src/chrome/browser/history/\
  # history_types.h
  VISIT_SOURCE = {
      0: 'SOURCE_SYNCED',
      1: 'SOURCE_BROWSED',
      2: 'SOURCE_EXTENSION',
      3: 'SOURCE_FIREFOX_IMPORTED',
      4: 'SOURCE_IE_IMPORTED',
      5: 'SOURCE_SAFARI_IMPORTED'
  }

  CORE_MASK = 0xff

  def _GetHostname(self, url):
    """Retrieves the hostname from a full URL.

    Args:
      url (str): full URL.

    Returns:
      str: hostname or full URL if not hostname could be retrieved.
    """
    if url.startswith('http') or url.startswith('ftp'):
      _, _, uri = url.partition('//')
      hostname, _, _ = uri.partition('/')
      return hostname

    if url.startswith('about') or url.startswith('chrome'):
      hostname, _, _ = url.partition('/')
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
      return ''

    url_cache_results = cache.GetResults('url')
    if not url_cache_results:
      result_set = database.Query(self.URL_CACHE_QUERY)

      cache.CacheQueryResults(result_set, 'url', 'id', ('url', 'title'))
      url_cache_results = cache.GetResults('url')

    reference_url, reference_title = url_cache_results.get(url, ['', ''])

    if not reference_url:
      return ''

    return '{0:s} ({1:s})'.format(reference_url, reference_title)

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

    sync_cache_results = cache.GetResults('sync')
    if not sync_cache_results:
      result_set = database.Query(self.SYNC_CACHE_QUERY)

      cache.CacheQueryResults(result_set, 'sync', 'id', ('source',))
      sync_cache_results = cache.GetResults('sync')

    results = sync_cache_results.get(visit_id, None)
    if results is None:
      return

    return self.VISIT_SOURCE.get(results[0], None)

  def ParseFileDownloadedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeHistoryFileDownloadedEventData()
    event_data.full_path = self._GetRowValue(query_hash, row, 'full_path')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.received_bytes = self._GetRowValue(
        query_hash, row, 'received_bytes')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'total_bytes')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    timestamp = self._GetRowValue(query_hash, row, 'start_time')
    date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseNewFileDownloadedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeHistoryFileDownloadedEventData()
    event_data.full_path = self._GetRowValue(query_hash, row, 'target_path')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.received_bytes = self._GetRowValue(
        query_hash, row, 'received_bytes')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'total_bytes')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    timestamp = self._GetRowValue(query_hash, row, 'start_time')
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseLastVisitedRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a last visited row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    extras = []

    hidden = self._GetRowValue(query_hash, row, 'hidden')
    transition = self._GetRowValue(query_hash, row, 'transition')

    transition_nr = transition & self.CORE_MASK
    page_transition = self.PAGE_TRANSITION.get(transition_nr, '')
    if page_transition:
      extras.append('Type: [{0:s} - {1:s}]'.format(
          page_transition, self.TRANSITION_LONGER.get(transition_nr, '')))

    if hidden == '1':
      extras.append('(url hidden)')

    # TODO: move to formatter.
    count = self._GetRowValue(query_hash, row, 'typed_count')
    if count >= 1:
      if count > 1:
        multi = 's'
      else:
        multi = ''

      extras.append('(type count {1:d} time{0:s})'.format(multi, count))
    else:
      extras.append('(URL not typed directly - no typed count)')

    visit_id = self._GetRowValue(query_hash, row, 'visit_id')
    from_visit = self._GetRowValue(query_hash, row, 'from_visit')
    url = self._GetRowValue(query_hash, row, 'url')

    visit_source = self._GetVisitSource(visit_id, cache, database)

    # TODO: replace extras by conditional formatting.
    event_data = ChromeHistoryPageVisitedEventData()
    event_data.extra = ' '.join(extras)
    event_data.from_visit = self._GetUrl(from_visit, cache, database)
    event_data.host = self._GetHostname(url)
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.typed_count = self._GetRowValue(query_hash, row, 'typed_count')
    event_data.url = self._GetRowValue(query_hash, row, 'url')
    event_data.visit_source = visit_source

    timestamp = self._GetRowValue(query_hash, row, 'visit_time')
    date_time = dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_LAST_VISITED)
    parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(ChromeHistoryPlugin)
