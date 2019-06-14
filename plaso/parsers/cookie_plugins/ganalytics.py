# -*- coding: utf-8 -*-
"""This file contains a plugin for parsing Google Analytics cookies."""

from __future__ import unicode_literals

import codecs

# pylint: disable=wrong-import-position
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager

if py2to3.PY_2:
  import urllib as urlparse
else:
  from urllib import parse as urlparse  # pylint: disable=no-name-in-module

# TODO: determine if __utmc always 0?


class GoogleAnalyticsEventData(events.EventData):
  """Google Analytics event data.

  Attributes:
    cookie_name (str): name of cookie.
    domain_hash (str): domain hash.
    pages_viewed (int): number of pages viewed.
    sessions (int): number of sessions.
    sources (int): number of sources.
    url (str): URL or path where the cookie got set.
    visitor_id (str): visitor identifier.
  """

  DATA_TYPE = 'cookie:google:analytics'

  def __init__(self, cookie_identifier):
    """Initializes event data.

    Args:
      cookie_identifier (str): unique identifier of the cookie.
    """
    data_type = '{0:s}:{1:s}'.format(self.DATA_TYPE, cookie_identifier)

    super(GoogleAnalyticsEventData, self).__init__(data_type=data_type)
    self.cookie_name = None
    self.domain_hash = None
    self.pages_viewed = None
    self.sessions = None
    self.sources = None
    self.url = None
    self.visitor_id = None


class GoogleAnalyticsUtmaPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utma Google Analytics cookies.

  The structure of the cookie data:
  <domain hash>.<visitor ID>.<first visit>.<previous visit>.<last visit>.
  <number of sessions>

  For example:
  137167072.1215918423.1383170166.1383170166.1383170166.1

  Or:
  <last visit>

  For example:
  13113225820000000
  """

  NAME = 'google_analytics_utma'
  DESCRIPTION = 'Google Analytics utma cookie parser'

  COOKIE_NAME = '__utma'

  URLS = [(
      'http://www.dfinews.com/articles/2012/02/'
      'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (str): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split('.')
    number_of_fields = len(fields)

    if number_of_fields not in (1, 6):
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
              number_of_fields, self.COOKIE_NAME))
      return

    if number_of_fields == 1:
      domain_hash = None
      visitor_identifier = None
      first_visit_posix_time = None
      previous_visit_posix_time = None

      try:
        # TODO: fix that we're losing precision here use dfdatetime.
        last_visit_posix_time = int(fields[0], 10) / 10000000
      except ValueError:
        last_visit_posix_time = None

      number_of_sessions = None

    elif number_of_fields == 6:
      domain_hash = fields[0]
      visitor_identifier = fields[1]

      # TODO: Double check this time is stored in UTC and not local time.
      try:
        first_visit_posix_time = int(fields[2], 10)
      except ValueError:
        first_visit_posix_time = None

      try:
        previous_visit_posix_time = int(fields[3], 10)
      except ValueError:
        previous_visit_posix_time = None

      try:
        last_visit_posix_time = int(fields[4], 10)
      except ValueError:
        last_visit_posix_time = None

      try:
        number_of_sessions = int(fields[5], 10)
      except ValueError:
        number_of_sessions = None

    event_data = GoogleAnalyticsEventData('utma')
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.sessions = number_of_sessions
    event_data.url = url
    event_data.visitor_id = visitor_identifier

    if first_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=first_visit_posix_time)
      event = time_events.DateTimeValuesEvent(
          date_time, 'Analytics Creation Time')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if previous_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=previous_visit_posix_time)
      event = time_events.DateTimeValuesEvent(
          date_time, 'Analytics Previous Time')
      parser_mediator.ProduceEventWithEventData(event, event_data)

    date_time = None
    if last_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=last_visit_posix_time)
      timestamp_description = definitions.TIME_DESCRIPTION_LAST_VISITED
    elif first_visit_posix_time is None and previous_visit_posix_time is None:
      # If both creation_time and written_time are None produce an event
      # object without a timestamp.
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME

    if date_time is not None:
      event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
      parser_mediator.ProduceEventWithEventData(event, event_data)


class GoogleAnalyticsUtmbPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmb Google Analytics cookies.

  The structure of the cookie data:
  <domain hash>.<pages viewed>.<unknown>.<last time>

  For example:
  137167072.1.10.1383170166
  173272373.6.8.1440489514899
  173272373.4.9.1373300660574

  Or:
  <last time>

  For example:
  13113225820000000
  """

  NAME = 'google_analytics_utmb'
  DESCRIPTION = 'Google Analytics utmb cookie parser'

  COOKIE_NAME = '__utmb'

  URLS = [(
      'http://www.dfinews.com/articles/2012/02/'
      'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split('.')
    number_of_fields = len(fields)

    if number_of_fields not in (1, 4):
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
              number_of_fields, self.COOKIE_NAME))
      return

    if number_of_fields == 1:
      domain_hash = None

      try:
        # TODO: fix that we're losing precision here use dfdatetime.
        last_visit_posix_time = int(fields[0], 10) / 10000000
      except ValueError:
        last_visit_posix_time = None

      number_of_pages_viewed = None

    elif number_of_fields == 4:
      domain_hash = fields[0]

      try:
        number_of_pages_viewed = int(fields[1], 10)
      except ValueError:
        number_of_pages_viewed = None

      try:
        if fields[2] in ('8', '9'):
          # TODO: fix that we're losing precision here use dfdatetime.
          last_visit_posix_time = int(fields[3], 10) / 1000
        else:
          last_visit_posix_time = int(fields[3], 10)
      except ValueError:
        last_visit_posix_time = None

    if last_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=last_visit_posix_time)
      timestamp_description = definitions.TIME_DESCRIPTION_LAST_VISITED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME

    event_data = GoogleAnalyticsEventData('utmb')
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.pages_viewed = number_of_pages_viewed
    event_data.url = url

    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class GoogleAnalyticsUtmtPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmt Google Analytics cookies.

  The structure of the cookie data:
  <last time>

  For example:
  13113215173000000
  """

  NAME = 'google_analytics_utmt'
  DESCRIPTION = 'Google Analytics utmt cookie parser'

  COOKIE_NAME = '__utmt'

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split('.')
    number_of_fields = len(fields)

    if number_of_fields != 1:
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
              number_of_fields, self.COOKIE_NAME))
      return

    try:
      # TODO: fix that we're losing precision here use dfdatetime.
      last_visit_posix_time = int(fields[0], 10) / 10000000
    except ValueError:
      last_visit_posix_time = None

    if last_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=last_visit_posix_time)
      timestamp_description = definitions.TIME_DESCRIPTION_LAST_VISITED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME

    event_data = GoogleAnalyticsEventData('utmt')
    event_data.cookie_name = self.COOKIE_NAME
    event_data.url = url

    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
    parser_mediator.ProduceEventWithEventData(event, event_data)


class GoogleAnalyticsUtmzPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmz Google Analytics cookies.

  The structure of the cookie data:
  <domain hash>.<last time>.<sessions>.<sources>.<variables>

  For example:
  207318870.1383170190.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|
  utmctr=(not%20provided)

  Or:
  <last time>

  For example:
  13128990382000000
  """

  NAME = 'google_analytics_utmz'
  DESCRIPTION = 'Google Analytics utmz cookie parser'

  COOKIE_NAME = '__utmz'

  URLS = [(
      'http://www.dfinews.com/articles/2012/02/'
      'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (str): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split('.')
    number_of_fields = len(fields)

    if number_of_fields > 5:
      variables = '.'.join(fields[4:])
      fields = fields[0:4]
      fields.append(variables)
      number_of_fields = len(fields)

    if number_of_fields not in (1, 5):
      parser_mediator.ProduceExtractionWarning(
          'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
              number_of_fields, self.COOKIE_NAME))
      return

    if number_of_fields == 1:
      domain_hash = None

      try:
        # TODO: fix that we're losing precision here use dfdatetime.
        last_visit_posix_time = int(fields[0], 10) / 10000000
      except ValueError:
        last_visit_posix_time = None

      number_of_sessions = None
      number_of_sources = None
      extra_attributes = {}

    elif number_of_fields == 5:
      domain_hash = fields[0]

      try:
        last_visit_posix_time = int(fields[1], 10)
      except ValueError:
        last_visit_posix_time = None

      try:
        number_of_sessions = int(fields[2], 10)
      except ValueError:
        number_of_sessions = None

      try:
        number_of_sources = int(fields[3], 10)
      except ValueError:
        number_of_sources = None

      extra_variables = fields[4].split('|')

      extra_attributes = {}
      for variable in extra_variables:
        key, _, value = variable.partition('=')

        # Urllib2 in Python 2 requires a 'str' argument, not 'unicode'. We thus
        # need to convert the value argument to 'str" and back again, but only
        # in Python 2.
        if isinstance(value, py2to3.UNICODE_TYPE) and py2to3.PY_2:
          try:
            value = codecs.decode(value, 'ascii')
          except UnicodeEncodeError:
            value = codecs.decode(value, 'ascii', errors='replace')
            parser_mediator.ProduceExtractionWarning(
                'Cookie contains non 7-bit ASCII characters, which have been '
                'replaced with a "?".')

        value = urlparse.unquote(value)

        if py2to3.PY_2:
          try:
            value = codecs.encode(value, 'utf-8')
          except UnicodeDecodeError:
            value = codecs.encode(value, 'utf-8', errors='replace')
            parser_mediator.ProduceExtractionWarning(
                'Cookie value did not contain a Unicode string. Non UTF-8 '
                'characters have been replaced.')

        extra_attributes[key] = value

    if last_visit_posix_time is not None:
      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=last_visit_posix_time)
      timestamp_description = definitions.TIME_DESCRIPTION_LAST_VISITED
    else:
      date_time = dfdatetime_semantic_time.SemanticTime('Not set')
      timestamp_description = definitions.TIME_DESCRIPTION_NOT_A_TIME

    event_data = GoogleAnalyticsEventData('utmz')
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.sessions = number_of_sessions
    event_data.sources = number_of_sources
    event_data.url = url

    for key, value in iter(extra_attributes.items()):
      setattr(event_data, key, value)

    event = time_events.DateTimeValuesEvent(date_time, timestamp_description)
    parser_mediator.ProduceEventWithEventData(event, event_data)


manager.CookiePluginsManager.RegisterPlugins([
    GoogleAnalyticsUtmaPlugin, GoogleAnalyticsUtmbPlugin,
    GoogleAnalyticsUtmtPlugin, GoogleAnalyticsUtmzPlugin])
