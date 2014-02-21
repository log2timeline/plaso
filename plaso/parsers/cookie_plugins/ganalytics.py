#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a plugin for parsing Google Analytics cookies."""

import urllib

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.cookie_plugins import interface


class GoogleAnalyticsEvent(event.PosixTimeEvent):
  """A simple placeholder for a Google Analytics event."""

  def __init__(self, timestamp, timestamp_desc, data_type, **kwargs):
    """Initialize a Google Analytics event."""
    super(GoogleAnalyticsEvent, self).__init__(
        timestamp, timestamp_desc, data_type)

    for key, value in kwargs.iteritems():
      setattr(self, key, value)


class GoogleAnalyticsUtmzPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'cookie_ganalytics_utmz'

  COOKIE_NAME = u'__utmz'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  # Google Analytics __utmz variable translation.
  # Taken from:
  #   http://www.dfinews.com/sites/dfinews.com/files/u739/Tab2Cookies020312.jpg
  GA_UTMZ_TRANSLATION = {
      'utmcsr': 'Last source used to access.',
      'utmccn': 'Ad campaign information.',
      'utmcmd': 'Last type of visit.',
      'utmctr': 'Keywords used to find site.',
      'utmcct': 'Path to the page of referring link.'}

  def GetEntries(self, cookie_data, **unused_kwargs):
    """Process the cookie."""
    # The structure of the field:
    #   <domain hash>.<last time>.<sessions>.<sources>.<variables>
    fields = cookie_data.split('.')

    if len(fields) > 5:
      variables = '.'.join(fields[4:])
      fields = fields[0:4]
      fields.append(variables)

    if len(fields) != 5:
      raise errors.WrongPlugin(u'Wrong number of fields. [{} vs. 5]'.format(
          len(fields)))

    domain_hash, last, sessions, sources, variables = fields
    extra_variables = variables.split('|')

    extra_variables_translated = []
    for variable in extra_variables:
      key, _, value = variable.partition('=')
      translation = self.GA_UTMZ_TRANSLATION.get(key, key)
      try:
        value_line = unicode(urllib.unquote(str(value)), 'utf-8')
      except UnicodeDecodeError:
        value_line = repr(value)

      extra_variables_translated.append(u'{} = {}'.format(
          translation, value_line))

    yield GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        self._data_type, domain_hash=domain_hash, sessions=int(sessions, 10),
        sources=int(sources, 10), extra=extra_variables_translated)


class GoogleAnalyticsUtmaPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'cookie_ganalytics_utma'

  COOKIE_NAME = u'__utma'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(self, cookie_data, **unused_kwargs):
    """Yield event objects extracted from the cookie."""
    # Values has the structure of:
    # <domain hash>.<visitor ID>.<first visit>.<previous>.<last>.<# of
    # sessions>
    fields = cookie_data.split('.')

    # Check for a valid record.
    if len(fields) != 6:
      raise errors.WrongPlugin(u'Wrong number of fields. [{} vs. 6]'.format(
          len(fields)))

    domain_hash, visitor_id, first_visit, previous, last, sessions = fields

    # TODO: Double check this time is stored in UTC and not local time.
    first_epoch = int(first_visit, 10)
    yield GoogleAnalyticsEvent(
        first_epoch, 'Analytics Creation Time', self._data_type,
        domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))

    yield GoogleAnalyticsEvent(
        int(previous, 10), 'Analytics Previous Time', self._data_type,
        domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))

    yield GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        self._data_type, domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))


class GoogleAnalyticsUtmbPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'cookie_ganalytics_utmb'

  COOKIE_NAME = u'__utmb'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(self, cookie_data, **unused_kwargs):
    """Yield event objects extracted from the cookie."""
    # Values has the structure of:
    #   <domain hash>.<pages viewed>.10.<last time>
    fields = cookie_data.split('.')

    # Check for a valid record.
    if len(fields) != 4:
      raise errors.WrongPlugin(u'Wrong number of fields. [{} vs. 4]'.format(
          len(fields)))

    domain_hash, pages_viewed, _, last = fields

    yield GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        self._data_type, domain_hash=domain_hash,
        pages_viewed=int(pages_viewed, 10))
