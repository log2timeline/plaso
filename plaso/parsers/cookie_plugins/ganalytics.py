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

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers.cookie_plugins import interface


class GoogleAnalyticsEvent(time_events.PosixTimeEvent):
  """A simple placeholder for a Google Analytics event."""

  DATA_TYPE = u'cookie:google:analytics'

  def __init__(
      self, timestamp, timestamp_desc, url, data_type_append, cookie_name,
      **kwargs):
    """Initialize a Google Analytics event.

    Args:
      timestamp: The timestamp in a POSIX format.
      timestamp_desc: A string describing the timestamp.
      url: The full URL where the cookie got set.
      data_type_append: String to append to the data type.
      cookie_name: The name of the cookie.
    """
    super(GoogleAnalyticsEvent, self).__init__(
        timestamp, timestamp_desc, u'{0:s}:{1:s}'.format(
            self.DATA_TYPE, data_type_append))

    self.url = url
    self.cookie_name = cookie_name

    for key, value in kwargs.iteritems():
      setattr(self, key, value)


class GoogleAnalyticsUtmzPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'google_analytics_utmz'

  COOKIE_NAME = u'__utmz'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_context, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_context: A parser context object (instance of ParserContext).
    """
    # The structure of the field:
    #   <domain hash>.<last time>.<sessions>.<sources>.<variables>
    fields = cookie_data.split('.')

    if len(fields) > 5:
      variables = u'.'.join(fields[4:])
      fields = fields[0:4]
      fields.append(variables)

    if len(fields) != 5:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 5]'.format(
          len(fields)))

    domain_hash, last, sessions, sources, variables = fields
    extra_variables = variables.split(u'|')

    kwargs = {}
    for variable in extra_variables:
      key, _, value = variable.partition(u'=')
      try:
        value_line = unicode(urllib.unquote(str(value)), 'utf-8')
      except UnicodeDecodeError:
        value_line = repr(value)

      kwargs[key] = value_line

    event_object = GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        url, 'utmz', self.COOKIE_NAME, domain_hash=domain_hash,
        sessions=int(sessions, 10), sources=int(sources, 10),
        **kwargs)
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


class GoogleAnalyticsUtmaPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'google_analytics_utma'

  COOKIE_NAME = u'__utma'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_context, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      cookie_data: Optional cookie data, as a byte string.
      url: Optional URL or path where the cookie got set.
    """
    # Values has the structure of:
    # <domain hash>.<visitor ID>.<first visit>.<previous>.<last>.<# of
    # sessions>
    fields = cookie_data.split(u'.')

    # Check for a valid record.
    if len(fields) != 6:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 6]'.format(
          len(fields)))

    domain_hash, visitor_id, first_visit, previous, last, sessions = fields

    # TODO: Double check this time is stored in UTC and not local time.
    first_epoch = int(first_visit, 10)
    event_object = GoogleAnalyticsEvent(
        first_epoch, 'Analytics Creation Time', url, 'utma', self.COOKIE_NAME,
        domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

    event_object = GoogleAnalyticsEvent(
        int(previous, 10), 'Analytics Previous Time', url, 'utma',
        self.COOKIE_NAME, domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)

    event_object = GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        url, 'utma', self.COOKIE_NAME, domain_hash=domain_hash,
        visitor_id=visitor_id, sessions=int(sessions, 10))
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


class GoogleAnalyticsUtmbPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'google_analytics_utmb'

  COOKIE_NAME = u'__utmb'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_context, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      cookie_data: Optional cookie data, as a byte string.
      url: Optional URL or path where the cookie got set.
    """
    # Values has the structure of:
    #   <domain hash>.<pages viewed>.10.<last time>
    fields = cookie_data.split(u'.')

    # Check for a valid record.
    if len(fields) != 4:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 4]'.format(
          len(fields)))

    domain_hash, pages_viewed, _, last = fields

    event_object = GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        url, 'utmb', self.COOKIE_NAME, domain_hash=domain_hash,
        pages_viewed=int(pages_viewed, 10))
    parser_context.ProduceEvent(event_object, plugin_name=self.NAME)
