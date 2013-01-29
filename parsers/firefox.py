#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser

# TODO: Add tests: firefox_test.py.


class FirefoxPlacesBookmarkAnnotation(event.EventContainer):
  """Convenience class for a Firefox bookmark annotation event container."""
  def __init__(self, row_id, title, url, content):
    """Initializes the event object.

    Args:
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      content: The content of the annotation.
    """
    super(FirefoxPlacesBookmarkAnnotation, self).__init__()
    self.data_type = 'firefox:places:bookmark_annotation'

    # TODO: refactor to formatter.
    self.source_short = 'WEBHIST'
    self.source_long = 'Firefox History'

    self.offset = row_id
    self.title = title
    self.url = url
    self.content = content


class FirefoxPlacesBookmarkFolder(event.EventContainer):
  """Convenience class for a Firefox bookmark folder event container."""
  def __init__(self, row_id, title):
    """Initializes the event object.

    Args:
      row_id: The identifier of the corresponding row.
      title: The title of the bookmark folder.
    """
    super(FirefoxPlacesBookmarkFolder, self).__init__()
    self.data_type = 'firefox:places:bookmark_folder'

    # TODO: refactor to formatter.
    self.source_short = 'WEBHIST'
    self.source_long = 'Firefox History'

    self.offset = row_id
    self.title = title


class FirefoxPlacesBookmark(event.EventContainer):
  """Convenience class for a Firefox bookmark event container."""
  # TODO: move to formatter.
  _TYPES = {
      1: 'URL',
      2: 'Folder',
      3: 'Separator',
  }
  _TYPES.setdefault('N/A')

  def __init__(self, row_id, type, title, url, places_title, hostname,
               visit_count):
    """Initializes the event object.

    Args:
      row_id: The identifier of the corresponding row.
      type: Integer value containing the bookmark type.
      title: The title of the bookmark folder.
      url: The bookmarked URL.
      places_title: The places title.
      hostname: The hostname.
      visit_count: The visit count.
    """
    super(FirefoxPlacesBookmark, self).__init__()
    self.data_type = 'firefox:places:bookmark'

    # TODO: refactor to formatter.
    self.source_short = 'WEBHIST'
    self.source_long = 'Firefox History'

    self.offset = row_id
    self.type = self._TYPES[type]
    self.title = title
    self.url = url
    self.places_title = places_title
    self.hostname = hostname
    self.visit_count = visit_count


class FirefoxPlacesPageVisitedEvent(event.EventObject):
  """Convenience class for a Firefox page visited event."""
  DATA_TYPE = 'firefox:places:page_visited'

  def __init__(self, timestamp, row_id, url, title, hostname, visit_count,
               extra):
    """Initializes the event object.

    Args:
      timestamp: The timestamp time value. The timestamp contains the
                 number of microseconds since Jan 1, 1970 00:00:00 UTC.
      row_id: The identifier of the corresponding row.
      url: The URL of the visited page.
      title: The title of the visited page.
      hostname: The visited hostname.
      visit_count: The visit count.
      extra: String containing extra event data (TODO refactor).
    """
    super(FirefoxPlacesPageVisitedEvent, self).__init__()

    self.timestamp = timestamp
    self.timestamp_desc = eventdata.EventTimestamp.PAGE_VISITED

    # TODO: refactor to formatter.
    self.source_short = 'WEBHIST'
    self.source_long = 'Firefox History'

    self.offset = row_id
    self.url = url
    self.title = title
    self.hostname = hostname
    self.visit_count = visit_count
    if extra:
      self.extra = u' %s' % extra


class FirefoxHistoryParser(parser.SQLiteParser):
  """Parses a Firefox history file.

     The Firefox history is stored in a SQLite database file named
     places.sqlite.
  """

  # TODO: is this still needed? if not remove.
  NAME = 'Firefox History'

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
  REQUIRED_TABLES = ('moz_places', 'moz_historyvisits', 'moz_bookmarks',
                     'moz_items_annos')

  # TODO: move to formatter.
  _URL_TYPES = {
      1: 'LINK',
      2: 'TYPED',
      3: 'BOOKMARK',
      4: 'EMBED',
      5: 'REDIRECT_PERMANENT',
      6: 'REDIRECT_TEMPORARY',
      7: 'DOWNLOAD'
  }
  _URL_TYPES.setdefault('N/A')

  __pychecker__ = 'unusednames=kwargs'
  def ParseBookmarkAnnotationRow(self, row, **kwargs):
    """Parses a bookmark annotation row.

    Args:
      row: The row resulting from the query.

    Returns:
      An event container (FirefoxPlacesBookmarkAnnotation) containing the event
      data.
    """
    container = FirefoxPlacesBookmarkAnnotation(
        row['id'], row['title'], row['url'], row['content'])

    container.Append(event.TimestampEvent(
        row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
        container.data_type))

    container.Append(event.TimestampEvent(
        row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        container.data_type))

    return container

  __pychecker__ = 'unusednames=kwargs'
  def ParseBookmarkFolderRow(self, row, **kwargs):
    """Parses a bookmark folder row.

    Args:
      row: The row resulting from the query.

    Returns:
      An event container (FirefoxPlacesBookmarkFolder) containing the event
      data.
    """
    container = FirefoxPlacesBookmarkFolder(
        row['id'], row['title'])

    container.Append(event.TimestampEvent(
        row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
        container.data_type))

    container.Append(event.TimestampEvent(
        row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        container.data_type))

    return container

  __pychecker__ = 'unusednames=kwargs'
  def ParseBookmarkRow(self, row, **kwargs):
    """Parses a bookmark row.

    Args:
      row: The row resulting from the query.

    Returns:
      An event container (FirefoxPlacesBookmark) containing the event data.
    """
    container = FirefoxPlacesBookmark(
        row['id'], row['type'], row['bookmark_title'], row['url'],
        row['places_title'], getattr(row, 'rev_host', 'N/A'),
        row['visit_count'])

    container.Append(event.TimestampEvent(
        row['dateAdded'], eventdata.EventTimestamp.ADDED_TIME,
        container.data_type))

    container.Append(event.TimestampEvent(
        row['lastModified'], eventdata.EventTimestamp.MODIFICATION_TIME,
        container.data_type))

    return container

  __pychecker__ = 'unusednames=kwargs'
  def ParsePageVisitedRow(self, row, **kwargs):
    """Parses a page visited row.

    Args:
      row: The row resulting from the query.

    Yields:
      An event object (FirefoxPlacesPageVisitedEvent) containing the event data.
    """
    # TODO: make extra conditional formatting.
    extras = []
    if row['from_visit']:
      extras.append(u'visited from: {0}'.format(
          self._GetUrl(row['from_visit'])))

    if row['hidden'] == '1':
      extras.append('(url hidden)')

    if row['typed'] == '1':
      extras.append('(directly typed)')
    else:
      extras.append('(URL not typed directly)')

    visit_type = row['visit_type']
    extras.append(self._URL_TYPES[visit_type])

    yield FirefoxPlacesPageVisitedEvent(
        row['visit_date'], row['id'], row['url'], row['title'],
        self._ReverseHostname(row['rev_host']), row['visit_count'],
        u' '.join(extras))

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
    if len(hostname) > 1:
      if hostname[-1] == '.':
        return hostname[::-1][1:]
      else:
        return hostname[::-1][0:]
    return hostname

  def _GetUrl(self, url_id):
    """Return an URL from a reference to an entry in the from_visit table."""
    query = ('SELECT url,rev_host,visit_date FROM moz_places, '
             'moz_historyvisits WHERE moz_places.id = '
             'moz_historyvisits.place_id AND moz_historyvisits.id=:id')

    cursor = self.db.cursor()
    result_set = cursor.execute(query, {'id': url_id})
    row = result_set.fetchone()

    if row:
      hostname = self._ReverseHostname(row['rev_host'])
      return u'%s (%s)' % (row['url'], hostname)
    return u''


class FirefoxBookmarkAnnotationFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite bookmark annotation."""
  DATA_TYPE = 'firefox:places:bookmark_annotation'

  FORMAT_STRING = (u'Bookmark Annotation: [{content}] to bookmark [{title}] '
                   u'({url})')
  FORMAT_STRING_SHORT = u'Bookmark Annotation: {title}'


class FirefoxBookmarkFolderFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite bookmark folder."""
  DATA_TYPE = 'firefox:places:bookmark_folder'

  FORMAT_STRING = '{title}'


class FirefoxBookmarkFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite URL bookmark."""
  DATA_TYPE = 'firefox:places:bookmark'

  FORMAT_STRING = (u'Bookmark {type} {title} ({url}) '
                   u'[{places_title}] visit count {visit_count}')
  FORMAT_STRING_SHORT = u'Bookmarked {title} ({url})'


class FirefoxPageVisitFormatter(eventdata.EventFormatter):
  """Formatter for a Firefox places.sqlite page visited."""
  DATA_TYPE = 'firefox:places:page_visited'

  # TODO: make extra conditional formatting.
  FORMAT_STRING = (u'{url} ({title}) [count: {visit_count}] '
                   u'Host: {hostname}{extra}')
  FORMAT_STRING_SHORT = u'URL: {url}'
