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
"""This file contains a firefox history parser in plaso."""
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class Firefox(parser.SQLiteParser):
  """Parse Firefox history files using SQLiteParser."""

  NAME = 'Firefox History'

  # Define the needed queries.
  QUERIES = [(('SELECT moz_historyvisits.id, moz_places.url,moz_places.title, '
               'moz_places.visit_count,moz_historyvisits.visit_date,'
               'moz_historyvisits.from_visit,moz_places.rev_host,'
               'moz_places.hidden,moz_places.typed,moz_historyvisits.visit_typ'
               'e FROM moz_places, moz_historyvisits WHERE moz_places.id = '
               'moz_historyvisits.place_id'), 'ParseVisitRecord'),
             (('SELECT moz_bookmarks.type,moz_bookmarks.title AS bookmark_titl'
               'e,moz_bookmarks.dateAdded,moz_bookmarks.lastModified,moz_plac'
               'es.url,moz_places.title AS places_title,moz_places.rev_host,'
               'moz_places.visit_count, moz_bookmarks.id FROM '
               'moz_places, moz_bookmarks WHERE moz_bookmarks.fk = '
               'moz_places.id AND moz_bookmarks.type <> 3'),
              'ParseBookmarkRecord'),
             (('SELECT moz_items_annos.content, moz_items_annos.dateAdded,'
               'moz_items_annos.lastModified,moz_bookmarks.title, '
               'moz_places.url,moz_places.rev_host, moz_items_annos.id FROM'
               ' moz_items_annos, moz_bookmarks,moz_places WHERE moz_items_'
               'annos.item_id = moz_bookmarks.id AND moz_bookmarks.fk = moz_'
               'places.id'),
              'ParseAnnotations'),
             (('SELECT moz_bookmarks.id, moz_bookmarks.title,moz_bookmarks.dat'
               'eAdded, moz_bookmarks.lastModified FROM moz_bookmarks WHERE'
               ' moz_bookmarks.type = 2'), 'ParseBookmarkFolder')]

  # The required tables.
  REQUIRED_TABLES = ('moz_places', 'moz_historyvisits', 'moz_bookmarks',
                     'moz_items_annos')

  URL_TYPES = {
      '1': 'LINK',
      '2': 'TYPED',
      '3': 'BOOKMARK',
      '4': 'EMBED',
      '5': 'REDIRECT_PERMANENT',
      '6': 'REDIRECT_TEMPORARY',
      '7': 'DOWNLOAD'
  }

  BOOKMARK_TYPES = {
      '1': 'URL',
      '2': 'Folder',
      '3': 'Separator'
  }

  def GetFormatStrings(self):
    """Return all format strings."""
    ret = []

    ret.append((
        '%s:BookmarkAnnotationAdded' % self.NAME,
        u'Bookmark Annotation: [{content}] to bookmark [{title}] ({url})',
        u'Bookmark Annotation: {title}'))
    ret.append((
        '%s:BookmarkAnnotationModified' % self.NAME,
        u'Bookmark Annotation: [{content}] to bookmark [{title}] ({url})',
        u'Bookmark Annotation: {title}'))

    ret.append(('%s:BookmarkFolderAdded' % self.NAME, '{title}'))
    ret.append(('%s:BookmarkFolderModified' % self.NAME, '{title}'))
    return ret

  def ParseAnnotations(self, row, **_):
    """Return an EventObject from the bookmark annotation table."""
    container = event.EventContainer()
    container.url = row['url']
    container.content = row['content']
    container.title = row['title']
    container.offset = row['id']

    evt = event.SQLiteEvent(
        row['dateAdded'], 'Bookmark Annotation Added', 'WEBHIST',
        self.NAME)
    container.Append(evt)

    evt = event.SQLiteEvent(
        row['lastModified'], 'Bookmark Annotation Modifed', 'WEBHIST',
        self.NAME)
    container.Append(evt)

    return container

  def ParseBookmarkFolder(self, row, **_):
    """Return an EventObject from a bookmark folder."""
    date = row['dateAdded']
    container = event.EventContainer()
    container.offset = row['id']
    container.title = row['title']

    evt = event.SQLiteEvent(
        date, 'Bookmark Folder Added', 'WEBHIST', self.NAME)
    container.Append(evt)

    date = row['lastModified']
    evt = event.SQLiteEvent(
        date, 'Bookmark Folder Modifed', 'WEBHIST', self.NAME)
    container.Append(evt)

    return container

  def ParseBookmarkRecord(self, row, **_):
    """Return an EventObject from a bookmark record."""
    hostname = row['rev_host']
    if not hostname:
      hostname = 'N/A'

    container = event.EventContainer()
    container.bookmark_title = row['bookmark_title']
    container.url = row['url']
    container.places_title = row['places_title']
    container.count = row['visit_count']
    container.hostname = hostname
    container.offset = row['id']
    container.bookmark_type = self.BOOKMARK_TYPES.get(str(row['type']), 'N/A')

    evt = event.SQLiteEvent(
        row['dateAdded'], 'URL Bookmark Added', 'WEBHIST', self.NAME)
    container.Append(evt)

    evt = event.SQLiteEvent(
        row['lastModified'], 'URL Bookmark Modifed', 'WEBHIST', self.NAME)
    container.Append(evt)

    return container

  def ParseVisitRecord(self, row, **_):
    """Return an EventObject from a visit record."""
    source = 'Page Visited'
    evt = event.SQLiteEvent(
        row['visit_date'], source, 'WEBHIST', self.NAME)

    evt.hostname = self._GetHostname(row['rev_host'])
    evt.url = row['url']
    evt.offset = row['id']

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

    extras.append(self.URL_TYPES.get(row['visit_type'], 'N/A'))

    evt.extra = u' '.join(extras)

    yield evt

  def _GetHostname(self, hostname):
    """Return a hostname from a reversed entry.

    The hostname entry is reversed:
      moc.elgoog.www.
    Should be:
      www.google.com

    Args:
      hostname: The reversed hostname.

    Returns:
      Reversed string with the first dot removed.
    """
    if not hostname:
      return ''

    return hostname[::-1][1:]

  def _GetUrl(self, url_id):
    """Return an URL from a reference to an entry in the from_visit table."""
    query = ('SELECT url,rev_host,visit_date FROM moz_places, '
             'moz_historyvisits WHERE moz_places.id = '
             'moz_historyvisits.place_id AND moz_historyvisits.id=:id')

    cursor = self.db.cursor()
    result_set = cursor.execute(query, {'id': url_id})
    row = result_set.fetchone()

    if row:
      hostname = self._GetHostname(row['rev_host'])
      return u'%s (%s)' % (row['url'], hostname)
    return u''


class FirefoxBookmarkAnnotationFormatter(eventdata.PlasoFormatter):
  """Define the formatting for Firefox history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Firefox:Firefox History:Bookmark Annotation', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'Bookmark Annotation: [{content}] to bookmark [{title}]'
                   ' ({url})')
  FORMAT_STRING_SHORT = u'Bookmark Annotation: {title}'


class FirefoxBookmarkFolderFormatter(eventdata.PlasoFormatter):
  """Define the formatting for Firefox history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Firefox:Firefox History:Bookmark Folder', re.DOTALL)

  # The format string.
  FORMAT_STRING = '{title}'


class FirefoxUrlBookmarkFormatter(eventdata.PlasoFormatter):
  """Define the formatting for Firefox history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Firefox:Firefox History:URL Bookmark', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'Bookmark {bookmark_type} {bookmark_title} ({url}) [{place'
                   's_title}] count {count}')
  FORMAT_STRING_SHORT = u'Bookmarked {bookmark_title} ({url})'


class FirefoxPageVisitFormatter(eventdata.PlasoFormatter):
  """Define the formatting for Firefox history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Firefox:Firefox History:Page Visited', re.DOTALL)

  # The format string.
  FORMAT_STRING = u'{url} ({title}) [count: {count}] Host: {hostname}{extra}'
  FORMAT_STRING_SHORT = u'URL: {url}'
