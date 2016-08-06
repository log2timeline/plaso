# -*- coding: utf-8 -*-
"""This file contains a plugin for parsing Google Analytics cookies."""

import urllib

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


# TODO: determine if __utmc always 0?


class GoogleAnalyticsEvent(time_events.PosixTimeEvent):
  """A simple placeholder for a Google Analytics event."""

  DATA_TYPE = u'cookie:google:analytics'

  def __init__(
      self, timestamp, timestamp_description, cookie_identifier, url,
      domain_hash=None, extra_attributes=None, number_of_pages_viewed=None,
      number_of_sessions=None, number_of_sources=None, visitor_identifier=None):
    """Initialize a Google Analytics event.

    Args:
      posix_time (int): POSIX time value, which contains the number of seconds
          since January 1, 1970 00:00:00 UTC.
      timestamp_description (str): description of the usage of the timestamp
          value.
      cookie_identifier (str): unique identifier of the cookie.
      url (str): URL or path where the cookie got set.
      domain_hash (Optional[str]): domain hash.
      extra_attributes (Optional[dict[str,str]]): extra attributes.
      number_of_pages_viewed (Optional[int]): number of pages viewed.
      number_of_sessions (Optional[int]): number of sessions.
      number_of_sources (Optional[int]): number of sources.
      visitor_identifier (Optional[str]): visitor identifier.
    """
    data_type = u'{0:s}:{1:s}'.format(self.DATA_TYPE, cookie_identifier)
    super(GoogleAnalyticsEvent, self).__init__(
        timestamp, timestamp_description, data_type=data_type)

    self.cookie_name = u'__{0:s}'.format(cookie_identifier)
    self.domain_hash = domain_hash
    self.pages_viewed = number_of_pages_viewed
    self.sessions = number_of_sessions
    self.sources = number_of_sources
    self.url = url
    self.visitor_id = visitor_identifier

    if not extra_attributes:
      return

    # TODO: refactor, this approach makes it very hard to tell
    # which values are actually set.
    for key, value in iter(extra_attributes.items()):
      setattr(self, key, value)


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

  NAME = u'google_analytics_utma'
  DESCRIPTION = u'Google Analytics utma cookie parser'

  COOKIE_NAME = u'__utma'

  URLS = [(
      u'http://www.dfinews.com/articles/2012/02/'
      u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields not in (1, 6):
      parser_mediator.ProduceExtractionError(
          u'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
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

    if first_visit_posix_time is not None:
      event_object = GoogleAnalyticsEvent(
          first_visit_posix_time, u'Analytics Creation Time', u'utma', url,
          domain_hash=domain_hash, number_of_sessions=number_of_sessions,
          visitor_identifier=visitor_identifier)
      parser_mediator.ProduceEvent(event_object)

    if previous_visit_posix_time is not None:
      event_object = GoogleAnalyticsEvent(
          previous_visit_posix_time, u'Analytics Previous Time', u'utma', url,
          domain_hash=domain_hash, number_of_sessions=number_of_sessions,
          visitor_identifier=visitor_identifier)
      parser_mediator.ProduceEvent(event_object)

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    elif first_visit_posix_time is None and previous_visit_posix_time is None:
      # If both creation_time and written_time are None produce an event
      # object without a timestamp.
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    if last_visit_posix_time is not None:
      event_object = GoogleAnalyticsEvent(
          last_visit_posix_time, timestamp_description, u'utma', url,
          domain_hash=domain_hash, number_of_sessions=number_of_sessions,
          visitor_identifier=visitor_identifier)
      parser_mediator.ProduceEvent(event_object)


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

  NAME = u'google_analytics_utmb'
  DESCRIPTION = u'Google Analytics utmb cookie parser'

  COOKIE_NAME = u'__utmb'

  URLS = [(
      u'http://www.dfinews.com/articles/2012/02/'
      u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields not in (1, 4):
      parser_mediator.ProduceExtractionError(
          u'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
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
        if fields[2] in (u'8', u'9'):
          # TODO: fix that we're losing precision here use dfdatetime.
          last_visit_posix_time = int(fields[3], 10) / 1000
        else:
          last_visit_posix_time = int(fields[3], 10)
      except ValueError:
        last_visit_posix_time = None

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    else:
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = GoogleAnalyticsEvent(
        last_visit_posix_time, timestamp_description, u'utmb', url,
        domain_hash=domain_hash, number_of_pages_viewed=number_of_pages_viewed)
    parser_mediator.ProduceEvent(event_object)


class GoogleAnalyticsUtmtPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmt Google Analytics cookies.

  The structure of the cookie data:
  <last time>

  For example:
  13113215173000000
  """

  NAME = u'google_analytics_utmt'
  DESCRIPTION = u'Google Analytics utmt cookie parser'

  COOKIE_NAME = u'__utmt'

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields != 1:
      parser_mediator.ProduceExtractionError(
          u'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
              number_of_fields, self.COOKIE_NAME))
      return

    try:
      # TODO: fix that we're losing precision here use dfdatetime.
      last_visit_posix_time = int(fields[0], 10) / 10000000
    except ValueError:
      last_visit_posix_time = None

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    else:
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = GoogleAnalyticsEvent(
        last_visit_posix_time, timestamp_description, u'utmt', url)
    parser_mediator.ProduceEvent(event_object)


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

  NAME = u'google_analytics_utmz'
  DESCRIPTION = u'Google Analytics utmz cookie parser'

  COOKIE_NAME = u'__utmz'

  URLS = [(
      u'http://www.dfinews.com/articles/2012/02/'
      u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      cookie_data (bytes): cookie data.
      url (str): URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields > 5:
      variables = u'.'.join(fields[4:])
      fields = fields[0:4]
      fields.append(variables)
      number_of_fields = len(fields)

    if number_of_fields not in (1, 5):
      parser_mediator.ProduceExtractionError(
          u'unsupported number of fields: {0:d} in cookie: {1:s}'.format(
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

      extra_variables = fields[4].split(u'|')

      extra_attributes = {}
      for variable in extra_variables:
        key, _, value = variable.partition(u'=')

        # Cookies can have a variety of different encodings, usually ASCII or
        # UTF-8, and values may additionally be URL encoded. urllib only
        # correctly url-decodes ASCII strings, so we'll convert our string
        # to ASCII first.
        try:
          ascii_value = value.encode(u'ascii')
        except UnicodeEncodeError:
          ascii_value = value.encode(u'ascii', errors=u'replace')
          parser_mediator.ProduceExtractionError(
              u'Cookie contains non 7-bit ASCII characters, which have been '
              u'replaced with a "?".')

        utf_stream = urllib.unquote(ascii_value)

        try:
          value_line = utf_stream.decode(u'utf-8')
        except UnicodeDecodeError:
          value_line = utf_stream.decode(u'utf-8', errors=u'replace')
          parser_mediator.ProduceExtractionError(
              u'Cookie value did not decode to Unicode string. Non UTF-8 '
              u'characters have been replaced.')

        extra_attributes[key] = value_line

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    else:
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = GoogleAnalyticsEvent(
        last_visit_posix_time, timestamp_description, u'utmz', url,
        domain_hash=domain_hash, extra_attributes=extra_attributes,
        number_of_sessions=number_of_sessions,
        number_of_sources=number_of_sources)
    parser_mediator.ProduceEvent(event_object)


manager.CookiePluginsManager.RegisterPlugins([
    GoogleAnalyticsUtmaPlugin, GoogleAnalyticsUtmbPlugin,
    GoogleAnalyticsUtmtPlugin, GoogleAnalyticsUtmzPlugin])
