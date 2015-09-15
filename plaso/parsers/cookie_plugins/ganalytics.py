# -*- coding: utf-8 -*-
"""This file contains a plugin for parsing Google Analytics cookies."""

import urllib

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


class GoogleAnalyticsEvent(time_events.PosixTimeEvent):
  """A simple placeholder for a Google Analytics event."""

  DATA_TYPE = u'cookie:google:analytics'

  def __init__(
      self, timestamp, timestamp_desc, cookie_identifier, url,
      domain_hash=None, number_of_pages_viewed=None, number_of_sessions=None,
      number_of_sources=None, visitor_identifier=None, **kwargs):
    """Initialize a Google Analytics event.

    Args:
      timestamp: The timestamp in a POSIX format.
      timestamp_desc: A string describing the timestamp.
      cookie_identifier: String to uniquely identify the cookie.
      url: The full URL where the cookie got set.
      domain_hash: optional domain hash.
      number_of_pages_viewed: optional number of pages viewed.
      number_of_sessions: optional number of sessions.
      number_of_sources: optional number of sources.
      visitor_identifier: optional visitor identifier.
    """
    data_type = u'{0:s}:{1:s}'.format(self.DATA_TYPE, cookie_identifier)
    super(GoogleAnalyticsEvent, self).__init__(
        timestamp, timestamp_desc, data_type=data_type)

    self.cookie_name = u'__{0:s}'.format(cookie_identifier)
    self.url = url
    self.domain_hash = domain_hash
    self.sessions = number_of_sessions
    self.sources = number_of_sources
    self.pages_viewed = number_of_pages_viewed
    self.visitor_id = visitor_identifier

    # TODO: refactor, this approach makes it very hard to tell
    # which values are actually set.
    for key, value in iter(kwargs.items()):
      setattr(self, key, value)


class GoogleAnalyticsUtmaPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utma Google Analytics cookies.

  The structure of the cookie data:
  <domain hash>.<visitor ID>.<first visit>.<previous>.<last>.<# of sessions>

  For example:
  137167072.1215918423.1383170166.1383170166.1383170166.1
  """

  NAME = u'google_analytics_utma'
  DESCRIPTION = u'Google Analytics utma cookie parser'

  COOKIE_NAME = u'__utma'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cookie_data: The cookie data, as a byte string.
      url: The full URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields != 6:
      raise errors.WrongPlugin(
          u'Wrong number of fields. [{0:d} vs. 6]'.format(number_of_fields))

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
      number_of_sessions = 0

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
  <domain hash>.<pages viewed>.10.<last time>

  For example:
  137167072.1.10.1383170166
  """

  NAME = u'google_analytics_utmb'
  DESCRIPTION = u'Google Analytics utmb cookie parser'

  COOKIE_NAME = u'__utmb'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cookie_data: The cookie data, as a byte string.
      url: The full URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields != 4:
      raise errors.WrongPlugin(
          u'Wrong number of fields. [{0:d} vs. 4]'.format(number_of_fields))

    domain_hash = fields[0]

    try:
      number_of_pages_viewed = int(fields[1], 10)
    except ValueError:
      number_of_pages_viewed = 0

    try:
      last_visit_posix_time = int(fields[3], 10)
    except ValueError:
      last_visit_posix_time = 0

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    else:
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = GoogleAnalyticsEvent(
        last_visit_posix_time, timestamp_description, u'utmb', url,
        domain_hash=domain_hash, number_of_pages_viewed=number_of_pages_viewed)
    parser_mediator.ProduceEvent(event_object)


class GoogleAnalyticsUtmzPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmz Google Analytics cookies.

  The structure of the cookie data:
  <domain hash>.<last time>.<sessions>.<sources>.<variables>

  For example:
  207318870.1383170190.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|
  utmctr=(not%20provided)
  """

  NAME = u'google_analytics_utmz'
  DESCRIPTION = u'Google Analytics utmz cookie parser'

  COOKIE_NAME = u'__utmz'

  # Point to few sources for URL information.
  URLS = [
      (u'http://www.dfinews.com/articles/2012/02/'
       u'google-analytics-cookies-and-forensic-implications')]

  def GetEntries(
      self, parser_mediator, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cookie_data: The cookie data, as a byte string.
      url: The full URL or path where the cookie got set.
    """
    fields = cookie_data.split(u'.')
    number_of_fields = len(fields)

    if number_of_fields > 5:
      variables = u'.'.join(fields[4:])
      fields = fields[0:4]
      fields.append(variables)
      number_of_fields = len(fields)

    if number_of_fields != 5:
      raise errors.WrongPlugin(
          u'Wrong number of fields. [{0:d} vs. 5]'.format(number_of_fields))

    domain_hash = fields[0]

    try:
      last_visit_posix_time = int(fields[1], 10)
    except ValueError:
      last_visit_posix_time = 0

    try:
      number_of_sessions = int(fields[2], 10)
    except ValueError:
      number_of_sessions = 0

    try:
      number_of_sources = int(fields[3], 10)
    except ValueError:
      number_of_sources = 0

    extra_variables = fields[4].split(u'|')

    kwargs = {}
    for variable in extra_variables:
      key, _, value = variable.partition(u'=')

      # Cookies can have a variety of different encodings, usually ASCII or
      # UTF-8, and values may additionally be URL encoded. urllib only correctly
      # url-decodes ASCII strings, so we'll convert our string to ASCII first.
      try:
        ascii_value = value.encode(u'ascii')
      except UnicodeEncodeError:
        ascii_value = value.encode(u'ascii', errors=u'ignore')
        parser_mediator.ProduceParseError(
            u'Cookie contains non 7-bit ASCII characters. The characters have '
            u'been removed')

      utf_stream = urllib.unquote(ascii_value)

      try:
        value_line = utf_stream.decode(u'utf-8')
      except UnicodeDecodeError:
        value_line = utf_stream.decode(u'utf-8', errors=u'replace')
        parser_mediator.ProduceParseError(
            u'Cookie value did not decode to value unicode string. Non UTF-8 '
            u'characters have been replaced.')

      kwargs[key] = value_line

    if last_visit_posix_time is not None:
      timestamp_description = eventdata.EventTimestamp.LAST_VISITED_TIME
    else:
      last_visit_posix_time = timelib.Timestamp.NONE_TIMESTAMP
      timestamp_description = eventdata.EventTimestamp.NOT_A_TIME

    event_object = GoogleAnalyticsEvent(
        last_visit_posix_time, timestamp_description, u'utmz', url,
        domain_hash=domain_hash, number_of_sessions=number_of_sessions,
        number_of_sources=number_of_sources, **kwargs)
    parser_mediator.ProduceEvent(event_object)


manager.CookiePluginsManager.RegisterPlugins([
    GoogleAnalyticsUtmaPlugin, GoogleAnalyticsUtmbPlugin,
    GoogleAnalyticsUtmzPlugin])
