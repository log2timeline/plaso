# -*- coding: utf-8 -*-
"""This file contains a plugin for parsing Google Analytics cookies."""

from urllib import parse as urlparse

from plaso.containers import events
from plaso.parsers.cookie_plugins import interface
from plaso.parsers.cookie_plugins import manager


# TODO: determine if __utmc always 0?


class GoogleAnalyticsUtmaEventData(events.EventData):
  """Google analytics __utma cookie event data.

  Attributes:
    cookie_name (str): name of cookie.
    domain_hash (str): domain hash.
    sessions (int): number of sessions.
    url (str): URL or path where the cookie got set.
    visited_times (list[dfdatetime.DateTimeValues]): dates and times the URL
        was visited.
    visitor_identifier (str): visitor identifier.
  """

  DATA_TYPE = 'cookie:google:analytics:utma'

  def __init__(self):
    """Initializes event data."""
    super(GoogleAnalyticsUtmaEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.domain_hash = None
    self.sessions = None
    self.url = None
    self.visited_times = None
    self.visitor_identifier = None


class GoogleAnalyticsUtmbEventData(events.EventData):
  """Google analytics __utmb cookie event data.

  Attributes:
    cookie_name (str): name of cookie.
    domain_hash (str): domain hash.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    pages_viewed (int): number of pages viewed.
    url (str): URL or path where the cookie got set.
  """

  DATA_TYPE = 'cookie:google:analytics:utmb'

  def __init__(self):
    """Initializes event data."""
    super(GoogleAnalyticsUtmbEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.domain_hash = None
    self.last_visited_time = None
    self.pages_viewed = None
    self.url = None


class GoogleAnalyticsUtmtEventData(events.EventData):
  """Google analytics __utmt cookie event data.

  Attributes:
    cookie_name (str): name of cookie.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    url (str): URL or path where the cookie got set.
  """

  DATA_TYPE = 'cookie:google:analytics:utmt'

  def __init__(self):
    """Initializes event data."""
    super(GoogleAnalyticsUtmtEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.last_visited_time = None
    self.url = None


class GoogleAnalyticsUtmzEventData(events.EventData):
  """Google analytics __utmz cookie event data.

  Attributes:
    cookie_name (str): name of cookie.
    domain_hash (str): domain hash.
    last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
        last visited.
    sessions (int): number of sessions.
    sources (int): number of sources.
    url (str): URL or path where the cookie got set.
  """

  DATA_TYPE = 'cookie:google:analytics:utmz'

  def __init__(self):
    """Initializes event data."""
    super(GoogleAnalyticsUtmzEventData, self).__init__(data_type=self.DATA_TYPE)
    self.cookie_name = None
    self.domain_hash = None
    self.last_visited_time = None
    self.sessions = None
    self.sources = None
    self.url = None


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
  DATA_FORMAT = 'Google Analytics __utma cookie'

  COOKIE_NAME = '__utma'

  def _ParseCookieData(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts events from cookie data.

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

    visited_times = []

    if number_of_fields == 1:
      domain_hash = None
      visitor_identifier = None
      number_of_sessions = None

      date_time = self._ParsePosixTimeIn100Nanoseconds(fields[0])
      if date_time:
        visited_times.append(date_time)

    elif number_of_fields == 6:
      domain_hash = fields[0]
      visitor_identifier = fields[1]

      # TODO: Double check this time is stored in UTC and not local time.
      date_time = self._ParsePosixTime(fields[2])
      if date_time:
        visited_times.append(date_time)

      date_time = self._ParsePosixTime(fields[3])
      if date_time:
        visited_times.append(date_time)

      date_time = self._ParsePosixTime(fields[4])
      if date_time:
        visited_times.append(date_time)

      number_of_sessions = self._ParseIntegerValue(fields[5])

    event_data = GoogleAnalyticsUtmaEventData()
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.sessions = number_of_sessions
    event_data.url = url
    event_data.visited_times = visited_times or None
    event_data.visitor_identifier = visitor_identifier

    parser_mediator.ProduceEventData(event_data)


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
  DATA_FORMAT = 'Google Analytics __utmb cookie'

  COOKIE_NAME = '__utmb'

  def _ParseCookieData(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts events from cookie data.

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
      number_of_pages_viewed = None

      date_time = self._ParsePosixTimeIn100Nanoseconds(fields[0])

    elif number_of_fields == 4:
      domain_hash = fields[0]

      number_of_pages_viewed = self._ParseIntegerValue(fields[1])

      if fields[2] in ('8', '9'):
        date_time = self._ParsePosixTimeInMilliseconds(fields[3])
      else:
        date_time = self._ParsePosixTime(fields[3])

    event_data = GoogleAnalyticsUtmbEventData()
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.last_visited_time = date_time
    event_data.pages_viewed = number_of_pages_viewed
    event_data.url = url

    parser_mediator.ProduceEventData(event_data)


class GoogleAnalyticsUtmtPlugin(interface.BaseCookiePlugin):
  """A browser cookie plugin for __utmt Google Analytics cookies.

  The structure of the cookie data:
  <last time>

  For example:
  13113215173000000
  """

  NAME = 'google_analytics_utmt'
  DATA_FORMAT = 'Google Analytics __utmt cookie'

  COOKIE_NAME = '__utmt'

  def _ParseCookieData(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts events from cookie data.

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

    event_data = GoogleAnalyticsUtmtEventData()
    event_data.cookie_name = self.COOKIE_NAME
    event_data.last_visited_time = self._ParsePosixTimeIn100Nanoseconds(
        fields[0])
    event_data.url = url

    parser_mediator.ProduceEventData(event_data)


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
  DATA_FORMAT = 'Google Analytics __utmz cookie'

  COOKIE_NAME = '__utmz'

  def _ParseCookieData(
      self, parser_mediator, cookie_data=None, url=None, **kwargs):
    """Extracts events from cookie data.

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
      number_of_sessions = None
      number_of_sources = None
      extra_attributes = {}

      date_time = self._ParsePosixTimeIn100Nanoseconds(fields[0])

    elif number_of_fields == 5:
      domain_hash = fields[0]

      date_time = self._ParsePosixTime(fields[1])

      number_of_sessions = self._ParseIntegerValue(fields[2])
      number_of_sources = self._ParseIntegerValue(fields[3])

      extra_variables = fields[4].split('|')

      extra_attributes = {}
      for variable in extra_variables:
        key, _, value = variable.partition('=')
        extra_attributes[key] = urlparse.unquote(value)

    event_data = GoogleAnalyticsUtmzEventData()
    event_data.cookie_name = self.COOKIE_NAME
    event_data.domain_hash = domain_hash
    event_data.last_visited_time = date_time
    event_data.sessions = number_of_sessions
    event_data.sources = number_of_sources
    event_data.url = url

    # TODO: explicitly define these as attributes of
    # GoogleAnalyticsUtmzEventData.
    for key, value in extra_attributes.items():
      setattr(event_data, key, value)

    parser_mediator.ProduceEventData(event_data)


manager.CookiePluginsManager.RegisterPlugins([
    GoogleAnalyticsUtmaPlugin, GoogleAnalyticsUtmbPlugin,
    GoogleAnalyticsUtmtPlugin, GoogleAnalyticsUtmzPlugin])
