# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Chrome history database files."""

from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import webkit_time as dfdatetime_webkit_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class ChromeHistoryFileDownloadedEventData(events.EventData):
  """Chrome History file downloaded event data.

  Attributes:
    danger_type (int): assessment by Safe Browsing of the danger of the
        downloaded content.
    end_time (dfdatetime.DateTimeValues): date and time the download was
        finished.
    full_path (str): full path where the file was downloaded to.
    interrupt_reason (int): indication why the download was interrupted.
    offset (str): identifier of the row, from which the event data was
        extracted.
    opened (int): value to indicate if the downloaded file was opened from
        the browser.
    query (str): SQL query that was used to obtain the event data.
    received_bytes (int): number of bytes received while downloading.
    start_time (dfdatetime.DateTimeValues): date and time the download was
        started.
    state (int): state of the download, such as finished or cancelled.
    total_bytes (int): total number of bytes to download.
    url (str): URL of the downloaded file.
  """

  DATA_TYPE = 'chrome:history:file_downloaded'

  def __init__(self):
    """Initializes event data."""
    super(ChromeHistoryFileDownloadedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.danger_type = None
    self.end_time = None
    self.full_path = None
    self.interrupt_reason = None
    self.offset = None
    self.opened = None
    self.query = None
    self.received_bytes = None
    self.start_time = None
    self.state = None
    self.total_bytes = None
    self.url = None


class ChromeHistoryPageVisitedEventData(events.EventData):
  """Chrome History page visited event data.

  Attributes:
    from_visit (str): URL where the visit originated from.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    offset (str): identifier of the row, from which the event data was
        extracted.
    page_transition_type (int): type of transitions between pages.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the visited page.
    typed_count (int): number of times the user has navigated to
        the page by typing in the address.
    url (str): URL of the visited page.
    url_hidden (bool): True if the URL is hidden.
    visit_count (int): number of times the user has navigated to this page.
    visit_source (int): source of the page visit.
  """

  DATA_TYPE = 'chrome:history:page_visited'

  def __init__(self):
    """Initializes event data."""
    super(ChromeHistoryPageVisitedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.from_visit = None
    self.last_visited_time = None
    self.offset = None
    self.page_transition_type = None
    self.query = None
    self.title = None
    self.typed_count = None
    self.url = None
    self.url_hidden = None
    self.visit_count = None
    self.visit_source = None


class BaseGoogleChromeHistoryPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Chrome history database files.

  The Google Chrome history database file is typically stored in:
  Archived History
  History

  Note that the Archived History database does not contain the downloads table.
  """

  _SYNC_CACHE_QUERY = 'SELECT id, source FROM visit_source'

  _URL_CACHE_QUERY = (
      'SELECT visits.id AS id, urls.url, urls.title FROM '
      'visits, urls WHERE urls.id = visits.url')

  # https://cs.chromium.org/chromium/src/ui/base/page_transition_types.h?l=108
  _PAGE_TRANSITION_CORE_MASK = 0xff

  def _GetPosixDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a POSIX date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def _GetWebKitDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a WebKit date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.WebKitTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_webkit_time.WebKitTime(timestamp=timestamp)

  def _GetUrl(self, url, cache, database):
    """Retrieves a URL from a reference to an entry in the from_visit table.

    Args:
      url (str): URL.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      str: URL or an empty string if no URL was found.
    """
    if not url:
      return ''

    url_cache_results = cache.GetResults('url')
    if not url_cache_results:
      result_set = database.Query(self._URL_CACHE_QUERY)

      cache.CacheQueryResults(result_set, 'url', 'id', ('url', 'title'))
      url_cache_results = cache.GetResults('url')

    reference_url, reference_title = url_cache_results.get(url, ['', ''])

    if not reference_url:
      return ''

    return '{0:s} ({1:s})'.format(reference_url, reference_title)

  def _GetVisitSource(self, visit_identifier, cache, database):
    """Retrieves a visit source type based on the identifier.

    Args:
      visit_identifier (str): identifier from the visits table for the
          particular record.
      cache (SQLiteCache): cache which contains cached results from querying
          the visit_source table.
      database (SQLiteDatabase): database.

    Returns:
      int: visit source type or None if no visit source type was found for
          the identifier.
    """
    sync_cache_results = cache.GetResults('sync')
    if not sync_cache_results:
      result_set = database.Query(self._SYNC_CACHE_QUERY)

      cache.CacheQueryResults(result_set, 'sync', 'id', ('source',))
      sync_cache_results = cache.GetResults('sync')

    if sync_cache_results and visit_identifier:
      results = sync_cache_results.get(visit_identifier, None)
      if results:
        return results[0]

    return None

  def ParseLastVisitedRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a last visited row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (SQLiteCache): cache which contains cached results from querying
          the visits and urls tables.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    hidden = self._GetRowValue(query_hash, row, 'hidden')
    transition = self._GetRowValue(query_hash, row, 'transition')

    visit_identifier = self._GetRowValue(query_hash, row, 'visit_id')
    from_visit = self._GetRowValue(query_hash, row, 'from_visit')

    event_data = ChromeHistoryPageVisitedEventData()
    event_data.from_visit = self._GetUrl(from_visit, cache, database)
    event_data.last_visited_time = self._GetWebKitDateTimeRowValue(
        query_hash, row, 'visit_time')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.page_transition_type = (
        transition & self._PAGE_TRANSITION_CORE_MASK)
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.typed_count = self._GetRowValue(query_hash, row, 'typed_count')
    event_data.url = self._GetRowValue(query_hash, row, 'url')
    event_data.url_hidden = hidden == '1'
    event_data.visit_count = self._GetRowValue(query_hash, row, 'visit_count')
    event_data.visit_source = self._GetVisitSource(
        visit_identifier, cache, database)

    parser_mediator.ProduceEventData(event_data)


class GoogleChrome8HistoryPlugin(BaseGoogleChromeHistoryPlugin):
  """SQLite parser plugin for Google Chrome 8 - 25 history database files."""

  NAME = 'chrome_8_history'
  DATA_FORMAT = 'Google Chrome 8 - 25 history SQLite database file'

  REQUIRED_STRUCTURE = {
      'downloads': frozenset([
          'id', 'full_path', 'received_bytes', 'total_bytes', 'url',
          'start_time', 'state']),
      'urls': frozenset([
          'id', 'url', 'title', 'visit_count', 'typed_count',
          'last_visit_time', 'hidden']),
      'visits': frozenset([
          'visit_time', 'from_visit', 'transition', 'id'])}

  QUERIES = [
      (('SELECT urls.id, urls.url, urls.title, urls.visit_count, '
        'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
        'visit_time, visits.from_visit, visits.transition, visits.id '
        'AS visit_id FROM urls, visits WHERE urls.id = visits.url ORDER '
        'BY visits.visit_time'), 'ParseLastVisitedRow'),
      (('SELECT id, full_path, url, start_time, received_bytes, '
        'total_bytes, state FROM downloads'), 'ParseFileDownloadedRow')]

  _SCHEMA_8 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,full_path '
          'LONGVARCHAR NOT NULL,url LONGVARCHAR NOT NULL,start_time INTEGER '
          'NOT NULL,received_bytes INTEGER NOT NULL,total_bytes INTEGER NOT '
          'NULL,state INTEGER NOT NULL)'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY '
          'KEY,value LONGVARCHAR)'),
      'presentation': (
          'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY,pres_index '
          'INTEGER NOT NULL)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL,pres_index INTEGER DEFAULT -1 NOT NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed BOOLEAN)')}

  _SCHEMA_16 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,full_path '
          'LONGVARCHAR NOT NULL,url LONGVARCHAR NOT NULL,start_time INTEGER '
          'NOT NULL,received_bytes INTEGER NOT NULL,total_bytes INTEGER NOT '
          'NULL,state INTEGER NOT NULL,end_time INTEGER NOT NULL,opened '
          'INTEGER NOT NULL)'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY '
          'KEY,value LONGVARCHAR)'),
      'presentation': (
          'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY,pres_index '
          'INTEGER NOT NULL)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL,pres_index INTEGER DEFAULT -1 NOT NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed BOOLEAN)')}

  _SCHEMA_19 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,full_path '
          'LONGVARCHAR NOT NULL,url LONGVARCHAR NOT NULL,start_time INTEGER '
          'NOT NULL,received_bytes INTEGER NOT NULL,total_bytes INTEGER NOT '
          'NULL,state INTEGER NOT NULL,end_time INTEGER NOT NULL,opened '
          'INTEGER NOT NULL)'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'presentation': (
          'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY,pres_index '
          'INTEGER NOT NULL)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL,pres_index INTEGER DEFAULT -1 NOT NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed BOOLEAN)')}

  _SCHEMA_20 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,full_path '
          'LONGVARCHAR NOT NULL,url LONGVARCHAR NOT NULL,start_time INTEGER '
          'NOT NULL,received_bytes INTEGER NOT NULL,total_bytes INTEGER NOT '
          'NULL,state INTEGER NOT NULL,end_time INTEGER NOT NULL,opened '
          'INTEGER NOT NULL)'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'presentation': (
          'CREATE TABLE presentation(url_id INTEGER PRIMARY KEY,pres_index '
          'INTEGER NOT NULL)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL,pres_index INTEGER DEFAULT -1 NOT NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed '
          'BOOLEAN,visit_duration INTEGER DEFAULT 0 NOT NULL)')}

  SCHEMAS = [_SCHEMA_8, _SCHEMA_16, _SCHEMA_19, _SCHEMA_20]

  def ParseFileDownloadedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
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
    event_data.start_time = self._GetPosixDateTimeRowValue(
        query_hash, row, 'start_time')
    event_data.state = self._GetRowValue(query_hash, row, 'state')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'total_bytes')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)


class GoogleChrome27HistoryPlugin(BaseGoogleChromeHistoryPlugin):
  """SQLite parser plugin for Google Chrome 27+ history database files."""

  NAME = 'chrome_27_history'
  DATA_FORMAT = 'Google Chrome 27 and later history SQLite database file'

  REQUIRED_STRUCTURE = {
      'downloads': frozenset([
          'id', 'target_path', 'received_bytes', 'total_bytes', 'start_time',
          'end_time', 'state', 'danger_type', 'interrupt_reason', 'opened']),
      'downloads_url_chains': frozenset([
          'id', 'url']),
      'urls': frozenset([
          'id', 'url', 'title', 'visit_count', 'typed_count',
          'last_visit_time', 'hidden']),
      'visits': frozenset([
          'visit_time', 'from_visit', 'transition', 'id'])}

  QUERIES = [
      (('SELECT urls.id, urls.url, urls.title, urls.visit_count, '
        'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
        'visit_time, visits.from_visit, visits.transition, visits.id '
        'AS visit_id FROM urls, visits WHERE urls.id = visits.url ORDER '
        'BY visits.visit_time'), 'ParseLastVisitedRow'),
      (('SELECT downloads.id AS id, downloads.start_time,'
        'downloads.target_path, downloads_url_chains.url, '
        'downloads.received_bytes, downloads.total_bytes, '
        'downloads.end_time, downloads.state, downloads.danger_type, '
        'downloads.interrupt_reason, downloads.opened FROM downloads,'
        ' downloads_url_chains WHERE downloads.id = '
        'downloads_url_chains.id'), 'ParseFileDownloadedRow')]

  _SCHEMA_27 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL, interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL)'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,is_indexed '
          'BOOLEAN,visit_duration INTEGER DEFAULT 0 NOT NULL)')}

  _SCHEMA_31 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL, interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL,referrer VARCHAR NOT NULL,by_ext_id '
          'VARCHAR NOT NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL)'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  _SCHEMA_37 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL,interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL,referrer VARCHAR NOT NULL,by_ext_id '
          'VARCHAR NOT NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL)'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  _SCHEMA_51 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,guid VARCHAR NOT '
          'NULL,current_path LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT '
          'NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT '
          'NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT '
          'NULL,danger_type INTEGER NOT NULL,interrupt_reason INTEGER NOT '
          'NULL,hash BLOB NOT NULL,end_time INTEGER NOT NULL,opened INTEGER '
          'NOT NULL,referrer VARCHAR NOT NULL,site_url VARCHAR NOT '
          'NULL,tab_url VARCHAR NOT NULL,tab_referrer_url VARCHAR NOT '
          'NULL,http_method VARCHAR NOT NULL,by_ext_id VARCHAR NOT '
          'NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL)'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  _SCHEMA_58 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,guid VARCHAR NOT '
          'NULL,current_path LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT '
          'NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT '
          'NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT '
          'NULL,danger_type INTEGER NOT NULL,interrupt_reason INTEGER NOT '
          'NULL,hash BLOB NOT NULL,end_time INTEGER NOT NULL,opened INTEGER '
          'NOT NULL,referrer VARCHAR NOT NULL,site_url VARCHAR NOT '
          'NULL,tab_url VARCHAR NOT NULL,tab_referrer_url VARCHAR NOT '
          'NULL,http_method VARCHAR NOT NULL,by_ext_id VARCHAR NOT '
          'NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,PRIMARY KEY '
          '(download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY,url LONGVARCHAR,title '
          'LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT NULL,typed_count '
          'INTEGER DEFAULT 0 NOT NULL,last_visit_time INTEGER NOT NULL,hidden '
          'INTEGER DEFAULT 0 NOT NULL,favicon_id INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  _SCHEMA_59 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,guid VARCHAR NOT '
          'NULL,current_path LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT '
          'NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT '
          'NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT '
          'NULL,danger_type INTEGER NOT NULL,interrupt_reason INTEGER NOT '
          'NULL,hash BLOB NOT NULL,end_time INTEGER NOT NULL,opened INTEGER '
          'NOT NULL,last_access_time INTEGER NOT NULL,transient INTEGER NOT '
          'NULL,referrer VARCHAR NOT NULL,site_url VARCHAR NOT NULL,tab_url '
          'VARCHAR NOT NULL,tab_referrer_url VARCHAR NOT NULL,http_method '
          'VARCHAR NOT NULL,by_ext_id VARCHAR NOT NULL,by_ext_name VARCHAR '
          'NOT NULL,etag VARCHAR NOT NULL,last_modified VARCHAR NOT '
          'NULL,mime_type VARCHAR(255) NOT NULL,original_mime_type '
          'VARCHAR(255) NOT NULL)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,PRIMARY KEY '
          '(download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  # Observed in Chrome 63.0.3239.108 meta.version 37
  _SCHEMA_63 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,guid VARCHAR NOT '
          'NULL,current_path LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT '
          'NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT '
          'NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT '
          'NULL,danger_type INTEGER NOT NULL,interrupt_reason INTEGER NOT '
          'NULL,hash BLOB NOT NULL,end_time INTEGER NOT NULL,opened INTEGER '
          'NOT NULL,referrer VARCHAR NOT NULL,site_url VARCHAR NOT '
          'NULL,tab_url VARCHAR NOT NULL,tab_referrer_url VARCHAR NOT '
          'NULL,http_method VARCHAR NOT NULL,by_ext_id VARCHAR NOT '
          'NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL, last_access_time '
          'INTEGER NOT NULL DEFAULT 0, transient INTEGER NOT NULL DEFAULT 0)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,PRIMARY KEY '
          '(download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE "urls"(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  # Observed in Chrome 65.0.3325.162
  _SCHEMA_65 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL,interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL,referrer VARCHAR NOT NULL,by_ext_id '
          'VARCHAR NOT NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL, guid VARCHAR NOT '
          'NULL DEFAULT \'\', hash BLOB NOT NULL DEFAULT X\'\', http_method '
          'VARCHAR NOT NULL DEFAULT \'\', tab_url VARCHAR NOT NULL '
          'DEFAULT \'\', tab_referrer_url VARCHAR NOT NULL DEFAULT \'\', '
          'site_url VARCHAR NOT NULL DEFAULT \'\', last_access_time INTEGER '
          'NOT NULL DEFAULT 0, transient INTEGER NOT NULL DEFAULT 0)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,PRIMARY KEY '
          '(download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE "urls"(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  # Observed in Chrome 67.0.3396.62.
  _SCHEMA_67 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL, interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL,referrer VARCHAR NOT NULL,by_ext_id '
          'VARCHAR NOT NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL, mime_type VARCHAR(255) NOT '
          'NULL DEFAULT "", original_mime_type VARCHAR(255) NOT NULL DEFAULT '
          '"", guid VARCHAR NOT NULL DEFAULT \'\', hash BLOB NOT NULL DEFAULT '
          'X\'\', http_method VARCHAR NOT NULL DEFAULT \'\', tab_url VARCHAR '
          'NOT NULL DEFAULT \'\', tab_referrer_url VARCHAR NOT NULL DEFAULT '
          '\'\', site_url VARCHAR NOT NULL DEFAULT \'\', last_access_time '
          'INTEGER NOT NULL DEFAULT 0, transient INTEGER NOT NULL DEFAULT 0)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL, finished INTEGER '
          'NOT NULL DEFAULT 0,PRIMARY KEY (download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE "urls"(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  # Observed in Linux Chrome 67.0.3396.99 meta.version 39
  _SCHEMA_67_2 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,current_path '
          'LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT NULL,start_time '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL,total_bytes '
          'INTEGER NOT NULL,state INTEGER NOT NULL,danger_type INTEGER NOT '
          'NULL,interrupt_reason INTEGER NOT NULL,end_time INTEGER NOT '
          'NULL,opened INTEGER NOT NULL,referrer VARCHAR NOT NULL,by_ext_id '
          'VARCHAR NOT NULL,by_ext_name VARCHAR NOT NULL,etag VARCHAR NOT '
          'NULL,last_modified VARCHAR NOT NULL,mime_type VARCHAR(255) NOT '
          'NULL,original_mime_type VARCHAR(255) NOT NULL, guid VARCHAR NOT '
          'NULL DEFAULT \'\', hash BLOB NOT NULL DEFAULT X\'\', http_method '
          'VARCHAR NOT NULL DEFAULT \'\', tab_url VARCHAR NOT NULL DEFAULT '
          '\'\', tab_referrer_url VARCHAR NOT NULL DEFAULT \'\', site_url '
          'VARCHAR NOT NULL DEFAULT \'\', last_access_time INTEGER NOT NULL '
          'DEFAULT 0, transient INTEGER NOT NULL DEFAULT 0)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL, finished INTEGER '
          'NOT NULL DEFAULT 0,PRIMARY KEY (download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE "urls"(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  # Observed in MacOS Chrome 67.0.3396.99 meta.version 39
  _SCHEMA_67_3 = {
      'downloads': (
          'CREATE TABLE downloads (id INTEGER PRIMARY KEY,guid VARCHAR NOT '
          'NULL,current_path LONGVARCHAR NOT NULL,target_path LONGVARCHAR NOT '
          'NULL,start_time INTEGER NOT NULL,received_bytes INTEGER NOT '
          'NULL,total_bytes INTEGER NOT NULL,state INTEGER NOT '
          'NULL,danger_type INTEGER NOT NULL,interrupt_reason INTEGER NOT '
          'NULL,hash BLOB NOT NULL,end_time INTEGER NOT NULL,opened INTEGER '
          'NOT NULL,last_access_time INTEGER NOT NULL,transient INTEGER NOT '
          'NULL,referrer VARCHAR NOT NULL,site_url VARCHAR NOT NULL,tab_url '
          'VARCHAR NOT NULL,tab_referrer_url VARCHAR NOT NULL,http_method '
          'VARCHAR NOT NULL,by_ext_id VARCHAR NOT NULL,by_ext_name VARCHAR '
          'NOT NULL,etag VARCHAR NOT NULL,last_modified VARCHAR NOT '
          'NULL,mime_type VARCHAR(255) NOT NULL,original_mime_type '
          'VARCHAR(255) NOT NULL)'),
      'downloads_slices': (
          'CREATE TABLE downloads_slices (download_id INTEGER NOT NULL,offset '
          'INTEGER NOT NULL,received_bytes INTEGER NOT NULL, finished INTEGER '
          'NOT NULL DEFAULT 0,PRIMARY KEY (download_id, offset) )'),
      'downloads_url_chains': (
          'CREATE TABLE downloads_url_chains (id INTEGER NOT NULL,chain_index '
          'INTEGER NOT NULL,url LONGVARCHAR NOT NULL, PRIMARY KEY (id, '
          'chain_index) )'),
      'keyword_search_terms': (
          'CREATE TABLE keyword_search_terms (keyword_id INTEGER NOT '
          'NULL,url_id INTEGER NOT NULL,lower_term LONGVARCHAR NOT NULL,term '
          'LONGVARCHAR NOT NULL)'),
      'meta': (
          'CREATE TABLE meta(key LONGVARCHAR NOT NULL UNIQUE PRIMARY KEY, '
          'value LONGVARCHAR)'),
      'segment_usage': (
          'CREATE TABLE segment_usage (id INTEGER PRIMARY KEY,segment_id '
          'INTEGER NOT NULL,time_slot INTEGER NOT NULL,visit_count INTEGER '
          'DEFAULT 0 NOT NULL)'),
      'segments': (
          'CREATE TABLE segments (id INTEGER PRIMARY KEY,name VARCHAR,url_id '
          'INTEGER NON NULL)'),
      'typed_url_sync_metadata': (
          'CREATE TABLE typed_url_sync_metadata (storage_key INTEGER PRIMARY '
          'KEY NOT NULL,value BLOB)'),
      'urls': (
          'CREATE TABLE urls(id INTEGER PRIMARY KEY AUTOINCREMENT,url '
          'LONGVARCHAR,title LONGVARCHAR,visit_count INTEGER DEFAULT 0 NOT '
          'NULL,typed_count INTEGER DEFAULT 0 NOT NULL,last_visit_time '
          'INTEGER NOT NULL,hidden INTEGER DEFAULT 0 NOT NULL)'),
      'visit_source': (
          'CREATE TABLE visit_source(id INTEGER PRIMARY KEY,source INTEGER '
          'NOT NULL)'),
      'visits': (
          'CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER NOT '
          'NULL,visit_time INTEGER NOT NULL,from_visit INTEGER,transition '
          'INTEGER DEFAULT 0 NOT NULL,segment_id INTEGER,visit_duration '
          'INTEGER DEFAULT 0 NOT NULL)')}

  SCHEMAS = [
      _SCHEMA_27, _SCHEMA_31, _SCHEMA_37, _SCHEMA_51, _SCHEMA_58, _SCHEMA_59,
      _SCHEMA_63, _SCHEMA_65, _SCHEMA_67, _SCHEMA_67_2, _SCHEMA_67_3]

  def ParseFileDownloadedRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = ChromeHistoryFileDownloadedEventData()
    event_data.danger_type = self._GetRowValue(query_hash, row, 'danger_type')
    event_data.end_time = self._GetWebKitDateTimeRowValue(
        query_hash, row, 'end_time')
    event_data.full_path = self._GetRowValue(query_hash, row, 'target_path')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.interrupt_reason = self._GetRowValue(
        query_hash, row, 'interrupt_reason')
    event_data.opened = self._GetRowValue(query_hash, row, 'opened')
    event_data.query = query
    event_data.received_bytes = self._GetRowValue(
        query_hash, row, 'received_bytes')
    event_data.start_time = self._GetWebKitDateTimeRowValue(
        query_hash, row, 'start_time')
    event_data.state = self._GetRowValue(query_hash, row, 'state')
    event_data.total_bytes = self._GetRowValue(query_hash, row, 'total_bytes')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugins([
    GoogleChrome8HistoryPlugin, GoogleChrome27HistoryPlugin])
