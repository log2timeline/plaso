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
"""This file contains a Chrome history parser in plaso."""
import re

from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser


class Chrome(parser.SQLiteParser):
  """Parse Chrome history files."""

  NAME = 'Chrome History'

  # Define the needed queries.
  QUERIES = [(('SELECT urls.id, urls.url, urls.title, urls.visit_count, '
               'urls.typed_count, urls.last_visit_time, urls.hidden, visits.'
               'visit_time, visits.from_visit, visits.transition FROM urls, '
               'visits WHERE urls.id = visits.url ORDER BY visits.visit_time'),
              'ParseVisitRecord'),
             (('SELECT id, full_path, url, start_time, received_bytes, '
               'total_bytes,state FROM downloads'), 'ParseDownloadRecord')]

  # The required tables.
  REQUIRED_TABLES = ('urls', 'visits', 'downloads')

  # The following definition for values can be found here:
  # http://src.chromium.org/svn/trunk/src/content/public/common/\
  # page_transition_types.h
  PAGE_TRANSITION = {
      '0': 'LINK',
      '1': 'TYPED',
      '2': 'AUTO_BOOKMARK',
      '3': 'AUTO_SUBFRAME',
      '4': 'MANUAL_SUBFRAME',
      '5': 'GENERATED',
      '6': 'START_PAGE',
      '7': 'FORM_SUBMIT',
      '8': 'RELOAD',
      '9': 'KEYWORD',
      '10': 'KEYWORD_GENERATED '
  }

  TRANSITION_LONGER = {
      '0': 'User clicked a link',
      '1': 'User typed the URL in the URL bar',
      '2': 'Got through a suggestion in the UI',
      '3': ('Content automatically loaded in a non-toplevel frame - user may '
            'not realize'),
      '4': 'Subframe explicitly requested by the user',
      '5': ('User typed in the URL bar and selected an entry from the list - '
            'such as a search bar'),
      '6': 'The start page of the browser',
      '7': 'A form the user has submitted values to',
      '8': ('The user reloaded the page, eg by hitting the reload button or '
            'restored a session'),
      '9': ('URL what was generated from a replaceable keyword other than the '
            'default search provider'),
      '10': 'Corresponds to a visit generated from a KEYWORD'
  }

  CORE_MASK = 0xff
  DATE_OFFSET = 11644473600000000

  def ParseDownloadRecord(self, row, **_):
    """Return an EventObject from a download record."""
    source = 'File Downloaded'

    date = int(row['start_time'] * 1e6)
    evt = event.SQLiteEvent(date, source, 'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.full_path = row['full_path']

    #TODO: Change this again to using the int value when the
    # plaso_storage_proto has been extended to allow int values for
    # attributes.
    evt.received_bytes = row['received_bytes']
    evt.total_bytes = row['total_bytes']
    evt.offset = row['id']

    yield evt

  def ParseVisitRecord(self, row, **_):
    """Return an EventObject from a visit record."""
    source = 'Page Visited'
    date = int(row['visit_time']) - self.DATE_OFFSET
    hostname = self._GetHostname(row['url'])
    extras = []

    if row['from_visit']:
      url = self._GetUrl(row['from_visit'])
      if url:
        extras.append(u'Visit from: %s ' % url)

    transition_nr = row['transition'] & self.CORE_MASK
    page_transition = self.PAGE_TRANSITION.get(transition_nr, '')
    if page_transition:
      extras.append(u'Type: [{0} - {1}]'.format(
          page_transition, self.TRANSITION_LONGER.get(transition_nr, '')))

    if row['hidden'] == '1':
      extras.append(u'(url hidden)')

    if int(row['typed_count']) >= 1:
      count = int(row['typed_count'])

      if count > 1:
        multi = u's'
      else:
        multi = u''

      extras.append(
          (u'(typed %d time{0} {1} - not indicating directly typed '
           'count)').format(multi, count))
    else:
      extras.append(u'(URL not typed directly - no typed count)')

    evt = event.SQLiteEvent(date, source, 'WEBHIST', self.NAME)
    evt.url = row['url']
    evt.title = row['title']
    evt.typed_count = row['typed_count']
    evt.hostname = hostname
    evt.extra = u' '.join(extras)
    evt.offset = row['id']

    yield evt

  def _GetHostname(self, hostname):
    """Return a hostname from a full URL."""
    # TODO: Fix this to provide a more error prone
    # and optimal method of extracting the hostname.
    # Often times the URL is an email address (mailto:...)
    # or a Chrome specific site: 'about:plugins'
    try:
      return hostname.split('/')[2]
    except IndexError:
      return 'N/A'

  def _GetUrl(self, url):
    """Return an URL from a reference to an entry in the from_visit table."""
    query = ('SELECT urls.url, urls.title, visits.visit_time FROM visits, urls'
             ' WHERE urls.id = visits.url AND visits.id=:id')

    cursor = self.db.cursor()
    result_set = cursor.execute(query, {'id': url})
    row = result_set.fetchone()

    if row:
      return u'%s (%s)' % (row['url'], row['title'])

    return u''


class ChromePageVisitedFormatter(eventdata.EventFormatter):
  """Define the formatting for Chrome history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Chrome:Chrome History:Page Visited', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'{url} ({title}) [count: {typed_count}] Host: '
                   '{hostname} {extra}')
  FORMAT_STRING_SHORT = u'{url} ({title})'


class ChromeFileDownloadFormatter(eventdata.EventFormatter):
  """Define the formatting for Chrome history."""

  # The indentifier for the formatter (a regular expression)
  ID_RE = re.compile('Chrome:Chrome History:File Downloaded', re.DOTALL)

  # The format string.
  FORMAT_STRING = (u'{url} ({full_path}). Total bytes received:{received_byt'
                   'es} (total:{total_bytes})')
  FORMAT_STRING_SHORT = u'{full_path} downloaded ({received_bytes} bytes)'
