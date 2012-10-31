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
from plaso.lib import event
from plaso.lib import parser


class ParseFirefox(parser.SQLiteParser):
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

  def ParseAnnotations(self, row, **_):
    """Return an EventObject from the bookmark annotation table."""
    text_long = u'Bookmark Annotation: [{0}] to bookmark [{1}] ({2})'.format(
        row['content'], row['title'], row['url'])
    text_short = u'Bookmark Annotation: {0}'.format(row['title'])

    evt = event.SQLiteEvent(
        row['dateAdded'], 'Bookmark Annotation Added', text_long, text_short,
        'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.offset = row['id']
    yield evt

    evt = event.SQLiteEvent(
        row['lastModified'], 'Bookmark Annotation Modifed', text_long,
        text_short, 'WEBHIST', self.NAME)
    evt.offset = row['id']
    evt.url = row['url']
    yield evt

  def ParseBookmarkFolder(self, row, **_):
    """Return an EventObject from a bookmark folder."""
    date = row['dateAdded']
    evt = event.SQLiteEvent(
        date, 'Bookmark Folder Added', row['title'], row['title'], 'WEBHIST',
        self.NAME)
    evt.offset = row['id']
    yield evt

    date = row['lastModified']
    evt = event.SQLiteEvent(
        date, 'Bookmark Folder Modifed', row['title'], row['title'],
        'WEBHIST', self.NAME)
    evt.offset = row['id']
    yield evt

  def ParseBookmarkRecord(self, row, **_):
    """Return an EventObject from a bookmark record."""
    hostname = row['rev_host']
    if not hostname:
      hostname = 'N/A'

    bookmark_type = self.BOOKMARK_TYPES.get(str(row['type']), 'N/A')

    text_long = u'Bookmark {0} {1} ({2}) [{3}] count {4}'.format(
        bookmark_type, row['bookmark_title'], row['url'], row['places_title'],
        row['visit_count'])

    text_short = u'Bookmarked {0} ({1})'.format(row['bookmark_title'],
                                                row['url'])

    evt = event.SQLiteEvent(
        row['dateAdded'], 'URL Bookmark Added', text_long,
        text_short, 'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.hostname = hostname
    evt.offset = row['id']
    yield evt

    evt = event.SQLiteEvent(
        row['lastModified'], 'URL Bookmark Modifed',
        text_long, text_short, 'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.hostname = hostname
    evt.offset = row['id']
    yield evt

  def ParseVisitRecord(self, row, **_):
    """Return an EventObject from a visit record."""
    source = 'Page Visited'
    hostname = self._GetHostname(row['rev_host'])
    if row['from_visit']:
      from_site = u' visited from: {0}'.format(
          self._GetUrl(row['from_visit']))
    else:
      from_site = ''

    if row['hidden'] == '1':
      hidden = ' (url hidden)'
    else:
      hidden = ''

    if row['typed'] == '1':
      typed = ' (directly typed)'
    else:
      typed = ' (URL not typed directly)'

    url_type = self.URL_TYPES.get(row['visit_type'], 'N/A')

    text_long = u'{0} ({1}) [count: {2}] Host: {3}{4}{5}{6}{7}'.format(
        row['url'], row['title'], row['visit_count'], hostname,
        from_site, hidden, typed, url_type)

    text_short = u'URL: %s' % row['url']

    evt = event.SQLiteEvent(
        row['visit_date'], source, text_long, text_short,
        'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.offset = row['id']
    evt.hostname = hostname

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
    return ''

