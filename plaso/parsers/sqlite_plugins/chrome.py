#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Parser for the Google Chrome History files.

   The Chrome History is stored in SQLite database files named History
   and Archived History. Where the Archived History does not contain
   the downloads table.
"""
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.sqlite_plugins import interface


class ChromeHistoryFileDownloadedEvent(event.EventObject):
  """Convenience class for a Chrome History file downloaded event."""
  DATA_TYPE = 'chrome:history:file_downloaded'

  def __init__(self, timestamp, row_id, url, full_path, received_bytes,
               total_bytes):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of seconds since Jan 1, 1970 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      url: The URL of the downloaded file.
      full_path: The full path where the file was downloaded to.
      received_bytes: The number of bytes received while downloading.
      total_bytes: The total number of bytes to download.
    """
    super(ChromeHistoryFileDownloadedEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.FILE_DOWNLOADED

    self.offset = row_id
    self.url = url
    self.full_path = full_path
    self.received_bytes = received_bytes
    self.total_bytes = total_bytes


class ChromeHistoryPageVisitedEvent(event.EventObject):
  """Convenience class for a Chrome History page visited event."""
  DATA_TYPE = 'chrome:history:page_visited'

  # TODO: refactor extra to be conditional arguments.
  def __init__(self, timestamp, row_id, url, title, hostname, typed_count,
               from_visit, extra, visit_source):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      url: The URL of the visited page.
      title: The title of the visited page.
      hostname: The visited hostname.
      typed_count: The number of charcters of the URL that were typed.
      from_visit: The URL where the visit originated from.
      extra: String containing extra event data.
      visit_source: The source of the page visit, if defined.
    """
    super(ChromeHistoryPageVisitedEvent, self).__init__()
    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.PAGE_VISITED

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

  NAME = 'chrome_history'

  # Define the needed queries.
  QUERIES = [(('SELECT urls.id, urls.url, urls.title, urls.visit_count, '
               'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
               'visit_time, visits.from_visit, visits.transition, visits.id '
               'AS visit_id FROM urls, visits WHERE urls.id = visits.url ORDER '
               'BY visits.visit_time'),
              'ParseLastVisitedRow'),
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
      0: u'SOURCE_SYNCED',
      1: u'SOURCE_BROWSED',
      2: u'SOURCE_EXTENSION',
      3: u'SOURCE_FIREFOX_IMPORTED',
      4: u'SOURCE_IE_IMPORTED',
      5: u'SOURCE_SAFARI_IMPORTED'
  }

  CORE_MASK = 0xff

  def ParseFileDownloadedRow(self, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (ChromeHistoryFileDownloadedEvent) containing the event
      data.
    """
    timestamp = timelib.Timestamp.FromPosixTime(row['start_time'])
    yield ChromeHistoryFileDownloadedEvent(
        timestamp, row['id'], row['url'], row['full_path'],
        row['received_bytes'], row['total_bytes'])

  def ParseNewFileDownloadedRow(self, row, **unused_kwargs):
    """Parses a file downloaded row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (ChromeHistoryFileDownloadedEvent) containing the event
      data.
    """
    timestamp = timelib.Timestamp.FromWebKitTime(row['start_time'])
    yield ChromeHistoryFileDownloadedEvent(
        timestamp, row['id'], row['url'], row['target_path'],
        row['received_bytes'], row['total_bytes'])

  def ParseLastVisitedRow(self, row, cache, database, **unused_kwargs):
    """Parses a last visited row.

    Args:
      row: The row resulting from the query.
      cache: A cache object (instance of SQLiteCache).
      database: A database object (instance of SQLiteDatabase).

    Yields:
      An event object (ChromeHistoryPageVisitedEvent) containing the event data.
    """
    extras = []

    transition_nr = row['transition'] & self.CORE_MASK
    page_transition = self.PAGE_TRANSITION.get(transition_nr, '')
    if page_transition:
      extras.append(u'Type: [{0} - {1}]'.format(
          page_transition, self.TRANSITION_LONGER.get(transition_nr, '')))

    if row['hidden'] == '1':
      extras.append(u'(url hidden)')

    count = row['typed_count']

    if count >= 1:
      if count > 1:
        multi = u's'
      else:
        multi = u''

      extras.append(
          u'(type count {1} time{0})'.format(multi, count))
    else:
      extras.append(u'(URL not typed directly - no typed count)')

    visit_source = self._GetVisitSource(row['visit_id'], cache, database)

    # TODO: replace extras by conditional formatting.
    yield ChromeHistoryPageVisitedEvent(
        timelib.Timestamp.FromWebKitTime(int(row['visit_time'])),
        row['id'], row['url'], row['title'], self._GetHostname(row['url']),
        row['typed_count'], self._GetUrl(
            row['from_visit'], cache, database), u' '.join(extras),
        visit_source)

  def _GetHostname(self, hostname):
    """Return a hostname from a full URL."""
    if hostname.startswith('http') or hostname.startswith('ftp'):
      _, _, uri = hostname.partition('//')
      hostname, _, _ = uri.partition('/')

      return hostname

    if hostname.startswith('about') or hostname.startswith('chrome'):
      site, _, _ = hostname.partition('/')
      return site

    return hostname

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

    sync_cache_results = cache.GetResults('sync')
    if not sync_cache_results:
      cursor = database.cursor
      result_set = cursor.execute(self.SYNC_CACHE_QUERY)
      cache.CacheQueryResults(
          result_set, 'sync', 'id', ('source',))
      sync_cache_results = cache.GetResults('sync')

    results = sync_cache_results.get(visit_id, None)
    if results is None:
      return

    return self.VISIT_SOURCE.get(results, None)

  def _GetUrl(self, url, cache, database):
    """Return an URL from a reference to an entry in the from_visit table."""
    if not url:
      return u''

    url_cache_results = cache.GetResults('url')
    if not url_cache_results:
      cursor = database.cursor
      result_set = cursor.execute(self.URL_CACHE_QUERY)
      cache.CacheQueryResults(
          result_set, 'url', 'id', ('url', 'title'))
      url_cache_results = cache.GetResults('url')

    reference_url, reference_title = url_cache_results.get(url, [u'', u''])

    if not reference_url:
      return u''

    return u'{} ({})'.format(reference_url, reference_title)
