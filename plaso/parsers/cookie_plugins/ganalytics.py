# -*- coding: utf-8 -*-
"""This file contains a plugin for parsing Google Analytics cookies."""

import urllib

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


class GoogleAnalyticsEvent(time_events.PosixTimeEvent):
  """A simple placeholder for a Google Analytics event."""

  DATA_TYPE = u'cookie:google:analytics'

  def __init__(
      self, timestamp, timestamp_desc, url, cookie_identifier, **kwargs):
    """Initialize a Google Analytics event.

    Args:
      timestamp: The timestamp in a POSIX format.
      timestamp_desc: A string describing the timestamp.
      url: The full URL where the cookie got set.
      cookie_identifier: String to uniquely identify the cookie.
    """
    data_type = u'{0:s}:{1:s}'.format(self.DATA_TYPE, cookie_identifier)
    super(GoogleAnalyticsEvent, self).__init__(
        timestamp, timestamp_desc, data_type)

    self.cookie_name = u'__{0:s}'.format(cookie_identifier)
    self.url = url

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

    # Check for a valid record.
    if len(fields) != 6:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 6]'.format(
          len(fields)))

    domain_hash, visitor_id, first_visit, previous_visit, last, sessions = (
        fields)

    # TODO: Double check this time is stored in UTC and not local time.
    try:
      first_posix_time = int(first_visit, 10)
    except ValueError:
      first_posix_time = None

    try:
      sessions = int(sessions, 10)
    except ValueError:
      sessions = 0

    try:
      previous_posix_time = int(previous_visit, 10)
    except ValueError:
      previous_posix_time = None

    try:
      last = int(last, 10)
    except ValueError:
      last = 0

    if first_posix_time is not None:
      event_object = GoogleAnalyticsEvent(
          first_posix_time, u'Analytics Creation Time', url, u'utma',
          domain_hash=domain_hash, visitor_id=visitor_id, sessions=sessions)
      parser_mediator.ProduceEvent(event_object)

    if previous_posix_time is not None:
      event_object = GoogleAnalyticsEvent(
          previous_posix_time, u'Analytics Previous Time', url, u'utma',
          domain_hash=domain_hash, visitor_id=visitor_id, sessions=sessions)
      parser_mediator.ProduceEvent(event_object)

    event_object = GoogleAnalyticsEvent(
        last, eventdata.EventTimestamp.LAST_VISITED_TIME, url, u'utma',
        domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=sessions)
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

    # Check for a valid record.
    if len(fields) != 4:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 4]'.format(
          len(fields)))

    domain_hash, pages_viewed, _, last = fields

    try:
      last = int(last, 10)
    except ValueError:
      last = 0

    try:
      pages_viewed = int(pages_viewed, 10)
    except ValueError:
      pages_viewed = 0

    event_object = GoogleAnalyticsEvent(
        last, eventdata.EventTimestamp.LAST_VISITED_TIME, url, u'utmb',
        domain_hash=domain_hash, pages_viewed=pages_viewed)
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

    try:
      last = int(last, 10)
    except ValueError:
      last = 0

    try:
      sessions = int(sessions, 10)
    except ValueError:
      sessions = 0

    try:
      sources = int(sources, 10)
    except ValueError:
      sources = 0

    event_object = GoogleAnalyticsEvent(
        last, eventdata.EventTimestamp.LAST_VISITED_TIME, url, u'utmz',
        domain_hash=domain_hash, sessions=sessions,
        sources=sources, **kwargs)
    parser_mediator.ProduceEvent(event_object)


manager.CookiePluginsManager.RegisterPlugins([
    GoogleAnalyticsUtmaPlugin, GoogleAnalyticsUtmbPlugin,
    GoogleAnalyticsUtmzPlugin])
