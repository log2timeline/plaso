# -*- coding: utf-8 -*-
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

    # TODO: refactor, this approach makes it very hard to tell
    # which values are actually set.
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
      self, parser_mediator, cookie_data=None, url=None, **unused_kwargs):
    """Extracts event objects from the cookie.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      cookie_data: The cookie data, as a byte string.
      url: The full URL or path where the cookie got set.
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
    parser_mediator.ProduceEvent(event_object)


class GoogleAnalyticsUtmaPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'google_analytics_utma'

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
    # Values has the structure of:
    # <domain hash>.<visitor ID>.<first visit>.<previous>.<last>.<# of
    # sessions>
    fields = cookie_data.split(u'.')

    # Check for a valid record.
    if len(fields) != 6:
      raise errors.WrongPlugin(u'Wrong number of fields. [{0:d} vs. 6]'.format(
          len(fields)))

    domain_hash, visitor_id, first_visit, previous, last, sessions = fields

    # TODO: catch int() throwing a ValueError.

    # TODO: Double check this time is stored in UTC and not local time.
    first_epoch = int(first_visit, 10)
    event_object = GoogleAnalyticsEvent(
        first_epoch, 'Analytics Creation Time', url, 'utma', self.COOKIE_NAME,
        domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))
    parser_mediator.ProduceEvent(event_object)

    event_object = GoogleAnalyticsEvent(
        int(previous, 10), 'Analytics Previous Time', url, 'utma',
        self.COOKIE_NAME, domain_hash=domain_hash, visitor_id=visitor_id,
        sessions=int(sessions, 10))
    parser_mediator.ProduceEvent(event_object)

    event_object = GoogleAnalyticsEvent(
        int(last, 10), eventdata.EventTimestamp.LAST_VISITED_TIME,
        url, 'utma', self.COOKIE_NAME, domain_hash=domain_hash,
        visitor_id=visitor_id, sessions=int(sessions, 10))
    parser_mediator.ProduceEvent(event_object)


class GoogleAnalyticsUtmbPlugin(interface.CookiePlugin):
  """A browser cookie plugin for Google Analytics cookies."""

  NAME = 'google_analytics_utmb'

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
    parser_mediator.ProduceEvent(event_object)
