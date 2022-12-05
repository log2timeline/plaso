# -*- coding: utf-8 -*-
"""SQLite parser plugin for Mozilla Firefox history database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class FirefoxPlacesBookmarkEventData(events.EventData):
  """Firefox bookmark event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the bookmark was
        added.
    host (str): visited hostname.
    modification_time (dfdatetime.DateTimeValues): date and time the bookmark
        was last modified.
    offset (str): identifier of the row, from which the event data was
        extracted.
    places_title (str): places title.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the bookmark folder.
    type (int): bookmark type.
    url (str): bookmarked URL.
    visit_count (int): visit count.
  """

  DATA_TYPE = 'firefox:places:bookmark'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxPlacesBookmarkEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.added_time = None
    self.host = None
    self.modification_time = None
    self.offset = None
    self.places_title = None
    self.query = None
    self.title = None
    self.type = None
    self.url = None
    self.visit_count = None


class FirefoxPlacesBookmarkAnnotationEventData(events.EventData):
  """Firefox bookmark annotation event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the bookmark
        annotation was added.
    content (str): annotation content.
    modification_time (dfdatetime.DateTimeValues): date and time the bookmark
        annotation was last modified.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the bookmark folder.
    url (str): bookmarked URL.
  """

  DATA_TYPE = 'firefox:places:bookmark_annotation'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxPlacesBookmarkAnnotationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.added_time = None
    self.content = None
    self.modification_time = None
    self.offset = None
    self.query = None
    self.title = None
    self.url = None


class FirefoxPlacesBookmarkFolderEventData(events.EventData):
  """Firefox bookmark folder event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the bookmark folder
        was added.
    modification_time (dfdatetime.DateTimeValues): date and time the bookmark
        folder was last modified.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the bookmark folder.
  """

  DATA_TYPE = 'firefox:places:bookmark_folder'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxPlacesBookmarkFolderEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.added_time = None
    self.modification_time = None
    self.offset = None
    self.query = None
    self.title = None


class FirefoxPlacesPageVisitedEventData(events.EventData):
  """Firefox page visited event data.

  Attributes:
    from_visit (str): URL that referred to the visited page.
    hidden (str): value to indicated if the URL was hidden.
    host (str): visited hostname.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    title (str): title of the visited page.
    typed (str): value to indicated if the URL was typed.
    url (str): URL of the visited page.
    visit_count (int): visit count.
    visit_type (str): transition type for the event.
  """

  DATA_TYPE = 'firefox:places:page_visited'

  def __init__(self):
    """Initializes event data."""
    super(FirefoxPlacesPageVisitedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.from_visit = None
    self.hidden = None
    self.host = None
    self.last_visited_time = None
    self.offset = None
    self.query = None
    self.title = None
    self.typed = None
    self.url = None
    self.visit_count = None
    self.visit_type = None


class FirefoxHistoryPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Mozilla Firefox history database files.

  The Mozilla Firefox history database file is typically stored in:
  places.sqlite
  """

  NAME = 'firefox_history'
  DATA_FORMAT = 'Mozilla Firefox history SQLite database (places.sqlite) file'

  REQUIRED_STRUCTURE = {
      'moz_places': frozenset([
          'url', 'title', 'visit_count', 'rev_host', 'hidden', 'typed', 'id']),
      'moz_historyvisits': frozenset([
          'id', 'visit_date', 'from_visit', 'visit_type', 'place_id']),
      'moz_bookmarks': frozenset([
          'type', 'title', 'dateAdded', 'lastModified', 'id', 'fk']),
      'moz_items_annos': frozenset([
          'content', 'dateAdded', 'lastModified', 'id', 'item_id'])}

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
        'FROM moz_places, moz_bookmarks '
        'WHERE moz_bookmarks.fk = moz_places.id AND moz_bookmarks.type <> 3'),
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

  _SCHEMA_V24 = {
      'moz_anno_attributes': (
          'CREATE TABLE moz_anno_attributes ( id INTEGER PRIMARY KEY, name '
          'VARCHAR(32) UNIQUE NOT NULL)'),
      'moz_annos': (
          'CREATE TABLE moz_annos ( id INTEGER PRIMARY KEY, place_id INTEGER '
          'NOT NULL, anno_attribute_id INTEGER, mime_type VARCHAR(32) DEFAULT '
          'NULL, content LONGVARCHAR, flags INTEGER DEFAULT 0, expiration '
          'INTEGER DEFAULT 0, type INTEGER DEFAULT 0, dateAdded INTEGER '
          'DEFAULT 0, lastModified INTEGER DEFAULT 0)'),
      'moz_bookmarks': (
          'CREATE TABLE moz_bookmarks ( id INTEGER PRIMARY KEY, type INTEGER, '
          'fk INTEGER DEFAULT NULL, parent INTEGER, position INTEGER, title '
          'LONGVARCHAR, keyword_id INTEGER, folder_type TEXT, dateAdded '
          'INTEGER, lastModified INTEGER)'),
      'moz_bookmarks_roots': (
          'CREATE TABLE moz_bookmarks_roots ( root_name VARCHAR(16) UNIQUE, '
          'folder_id INTEGER)'),
      'moz_favicons': (
          'CREATE TABLE moz_favicons ( id INTEGER PRIMARY KEY, url '
          'LONGVARCHAR UNIQUE, data BLOB, mime_type VARCHAR(32), expiration '
          'LONG)'),
      'moz_historyvisits': (
          'CREATE TABLE moz_historyvisits ( id INTEGER PRIMARY KEY, '
          'from_visit INTEGER, place_id INTEGER, visit_date INTEGER, '
          'visit_type INTEGER, session INTEGER)'),
      'moz_inputhistory': (
          'CREATE TABLE moz_inputhistory ( place_id INTEGER NOT NULL, input '
          'LONGVARCHAR NOT NULL, use_count INTEGER, PRIMARY KEY (place_id, '
          'input))'),
      'moz_items_annos': (
          'CREATE TABLE moz_items_annos ( id INTEGER PRIMARY KEY, item_id '
          'INTEGER NOT NULL, anno_attribute_id INTEGER, mime_type VARCHAR(32) '
          'DEFAULT NULL, content LONGVARCHAR, flags INTEGER DEFAULT 0, '
          'expiration INTEGER DEFAULT 0, type INTEGER DEFAULT 0, dateAdded '
          'INTEGER DEFAULT 0, lastModified INTEGER DEFAULT 0)'),
      'moz_keywords': (
          'CREATE TABLE moz_keywords ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'keyword TEXT UNIQUE)'),
      'moz_places': (
          'CREATE TABLE moz_places ( id INTEGER PRIMARY KEY, url LONGVARCHAR, '
          'title LONGVARCHAR, rev_host LONGVARCHAR, visit_count INTEGER '
          'DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL, typed INTEGER '
          'DEFAULT 0 NOT NULL, favicon_id INTEGER, frecency INTEGER DEFAULT '
          '-1 NOT NULL, last_visit_date INTEGER )')}

  _SCHEMA_V25 = {
      'moz_anno_attributes': (
          'CREATE TABLE moz_anno_attributes ( id INTEGER PRIMARY KEY, name '
          'VARCHAR(32) UNIQUE NOT NULL)'),
      'moz_annos': (
          'CREATE TABLE moz_annos ( id INTEGER PRIMARY KEY, place_id INTEGER '
          'NOT NULL, anno_attribute_id INTEGER, mime_type VARCHAR(32) DEFAULT '
          'NULL, content LONGVARCHAR, flags INTEGER DEFAULT 0, expiration '
          'INTEGER DEFAULT 0, type INTEGER DEFAULT 0, dateAdded INTEGER '
          'DEFAULT 0, lastModified INTEGER DEFAULT 0)'),
      'moz_bookmarks': (
          'CREATE TABLE moz_bookmarks ( id INTEGER PRIMARY KEY, type INTEGER, '
          'fk INTEGER DEFAULT NULL, parent INTEGER, position INTEGER, title '
          'LONGVARCHAR, keyword_id INTEGER, folder_type TEXT, dateAdded '
          'INTEGER, lastModified INTEGER, guid TEXT)'),
      'moz_bookmarks_roots': (
          'CREATE TABLE moz_bookmarks_roots ( root_name VARCHAR(16) UNIQUE, '
          'folder_id INTEGER)'),
      'moz_favicons': (
          'CREATE TABLE moz_favicons ( id INTEGER PRIMARY KEY, url '
          'LONGVARCHAR UNIQUE, data BLOB, mime_type VARCHAR(32), expiration '
          'LONG, guid TEXT)'),
      'moz_historyvisits': (
          'CREATE TABLE moz_historyvisits ( id INTEGER PRIMARY KEY, '
          'from_visit INTEGER, place_id INTEGER, visit_date INTEGER, '
          'visit_type INTEGER, session INTEGER)'),
      'moz_hosts': (
          'CREATE TABLE moz_hosts ( id INTEGER PRIMARY KEY, host TEXT NOT '
          'NULL UNIQUE, frecency INTEGER, typed INTEGER NOT NULL DEFAULT 0, '
          'prefix TEXT)'),
      'moz_inputhistory': (
          'CREATE TABLE moz_inputhistory ( place_id INTEGER NOT NULL, input '
          'LONGVARCHAR NOT NULL, use_count INTEGER, PRIMARY KEY (place_id, '
          'input))'),
      'moz_items_annos': (
          'CREATE TABLE moz_items_annos ( id INTEGER PRIMARY KEY, item_id '
          'INTEGER NOT NULL, anno_attribute_id INTEGER, mime_type VARCHAR(32) '
          'DEFAULT NULL, content LONGVARCHAR, flags INTEGER DEFAULT 0, '
          'expiration INTEGER DEFAULT 0, type INTEGER DEFAULT 0, dateAdded '
          'INTEGER DEFAULT 0, lastModified INTEGER DEFAULT 0)'),
      'moz_keywords': (
          'CREATE TABLE moz_keywords ( id INTEGER PRIMARY KEY AUTOINCREMENT, '
          'keyword TEXT UNIQUE)'),
      'moz_places': (
          'CREATE TABLE moz_places ( id INTEGER PRIMARY KEY, url LONGVARCHAR, '
          'title LONGVARCHAR, rev_host LONGVARCHAR, visit_count INTEGER '
          'DEFAULT 0, hidden INTEGER DEFAULT 0 NOT NULL, typed INTEGER '
          'DEFAULT 0 NOT NULL, favicon_id INTEGER, frecency INTEGER DEFAULT '
          '-1 NOT NULL, last_visit_date INTEGER , guid TEXT)'),
      'sqlite_stat1': (
          'CREATE TABLE sqlite_stat1(tbl, idx, stat)')}

  SCHEMAS = [_SCHEMA_V24, _SCHEMA_V25]

  # Cache queries.
  URL_CACHE_QUERY = (
      'SELECT h.id AS id, p.url, p.rev_host FROM moz_places p, '
      'moz_historyvisits h WHERE p.id = h.place_id')

  # TODO: move to formatter.
  _BOOKMARK_TYPES = {
      1: 'URL',
      2: 'Folder',
      3: 'Separator'}

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a POSIX time in microseconds date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value or None if not
          available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

  def _GetUrl(self, url_id, cache, database):
    """Retrieves a URL from a reference to an entry in the from_visit table.

    Args:
      url_id (str): identifier of the visited URL.
      cache (SQLiteCache): cache.
      database (SQLiteDatabase): database.

    Returns:
      str: URL and hostname.
    """
    url_cache_results = cache.GetResults('url')
    if not url_cache_results:
      result_set = database.Query(self.URL_CACHE_QUERY)

      cache.CacheQueryResults(
          result_set, 'url', 'id', ('url', 'rev_host'))
      url_cache_results = cache.GetResults('url')

    url, reverse_host = url_cache_results.get(url_id, ['', ''])

    if not url:
      return ''

    hostname = self._ReverseHostname(reverse_host)
    return '{0:s} ({1:s})'.format(url, hostname)

  def _ReverseHostname(self, hostname):
    """Reverses the hostname and strips the leading dot.

    The hostname entry is reversed:
      moc.elgoog.www.
    Should be:
      www.google.com

    Args:
      hostname (str): reversed hostname.

    Returns:
      str: hostname without a leading dot.
    """
    if not hostname:
      return ''

    if len(hostname) <= 1:
      return hostname

    if hostname[-1] == '.':
      return hostname[::-1][1:]

    return hostname[::-1][0:]

  def ParseBookmarkAnnotationRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a bookmark annotation row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = FirefoxPlacesBookmarkAnnotationEventData()
    event_data.added_time = self._GetDateTimeRowValue(
        query_hash, row, 'dateAdded')
    event_data.content = self._GetRowValue(query_hash, row, 'content')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastModified')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    parser_mediator.ProduceEventData(event_data)

  def ParseBookmarkFolderRow(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses a bookmark folder row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    title = self._GetRowValue(query_hash, row, 'title')

    event_data = FirefoxPlacesBookmarkFolderEventData()
    event_data.added_time = self._GetDateTimeRowValue(
        query_hash, row, 'dateAdded')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastModified')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.title = title or 'N/A'

    parser_mediator.ProduceEventData(event_data)

  def ParseBookmarkRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a bookmark row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    rev_host = self._GetRowValue(query_hash, row, 'rev_host')
    bookmark_type = self._GetRowValue(query_hash, row, 'type')

    event_data = FirefoxPlacesBookmarkEventData()
    event_data.added_time = self._GetDateTimeRowValue(
        query_hash, row, 'dateAdded')
    event_data.host = rev_host or 'N/A'
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastModified')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.places_title = self._GetRowValue(query_hash, row, 'places_title')
    event_data.query = query
    event_data.title = self._GetRowValue(query_hash, row, 'bookmark_title')
    event_data.type = self._BOOKMARK_TYPES.get(bookmark_type, 'N/A')
    event_data.url = self._GetRowValue(query_hash, row, 'url')
    event_data.visit_count = self._GetRowValue(query_hash, row, 'visit_count')

    parser_mediator.ProduceEventData(event_data)

  def ParsePageVisitedRow(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a page visited row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    from_visit = self._GetRowValue(query_hash, row, 'from_visit')
    if from_visit is not None:
      from_visit = self._GetUrl(from_visit, cache, database)

    rev_host = self._GetRowValue(query_hash, row, 'rev_host')

    event_data = FirefoxPlacesPageVisitedEventData()
    event_data.from_visit = from_visit
    event_data.hidden = self._GetRowValue(query_hash, row, 'hidden')
    event_data.host = self._ReverseHostname(rev_host)
    event_data.last_visited_time = self._GetDateTimeRowValue(
        query_hash, row, 'visit_date')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.typed = self._GetRowValue(query_hash, row, 'typed')
    event_data.url = self._GetRowValue(query_hash, row, 'url')
    event_data.visit_count = self._GetRowValue(query_hash, row, 'visit_count')
    event_data.visit_type = self._GetRowValue(query_hash, row, 'visit_type')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(FirefoxHistoryPlugin)
