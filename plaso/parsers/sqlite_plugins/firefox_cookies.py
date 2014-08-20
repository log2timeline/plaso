#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Parser for the Firefox Cookie database."""

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
# Register the cookie plugins.
from plaso.parsers import cookie_plugins  # pylint: disable=unused-import
from plaso.parsers.cookie_plugins import interface as cookie_interface
from plaso.parsers.sqlite_plugins import interface


class FirefoxCookieEvent(time_events.TimestampEvent):
  """Convenience class for a Firefox Cookie event."""

  DATA_TYPE = 'firefox:cookie:entry'

  def __init__(
      self, timestamp, usage, hostname, cookie_name, value, path, secure,
      httponly):
    """Initializes the event.

    Args:
      timestamp: The timestamp value in WebKit format..
      usage: Timestamp description string.
      hostname: The hostname of host that set the cookie value.
      cookie_name: The name field of the cookie.
      value: The value of the cookie.
      path: An URI of the page that set the cookie.
      secure: Indication if this cookie should only be transmitted over a secure
              channel.
      httponly: An indication that the cookie cannot be accessed through client
                side script.
    """
    super(FirefoxCookieEvent, self).__init__(timestamp, usage)
    if hostname.startswith('.'):
      hostname = hostname[1:]

    self.host = hostname
    self.cookie_name = cookie_name
    self.data = value
    self.path = path
    self.secure = True if secure else False
    self.httponly = True if httponly else False

    if self.secure:
      scheme = u'https'
    else:
      scheme = u'http'

    self.url = u'{0:s}://{1:s}{2:s}'.format(scheme, hostname, path)


class FirefoxCookiePlugin(interface.SQLitePlugin):
  """Parse Firefox Cookies file."""

  NAME = 'firefox_cookies'

  # Define the needed queries.
  QUERIES = [((
      'SELECT id, baseDomain, name, value, host, path, expiry, lastAccessed, '
      'creationTime, isSecure, isHttpOnly FROM moz_cookies'), 'ParseCookieRow')]

  # The required tables common to Archived History and History.
  REQUIRED_TABLES = frozenset(['moz_cookies'])

  # Point to few sources for URL information.
  URLS = [
      (u'https://hg.mozilla.org/mozilla-central/file/349a2f003529/netwerk/'
       u'cookie/nsCookie.h')]

  def __init__(self):
    """Initializes a plugin object."""
    super(FirefoxCookiePlugin, self).__init__()
    self._cookie_plugins = cookie_interface.GetPlugins()

  def ParseCookieRow(self, parser_context, row, **unused_kwargs):
    """Parses a cookie row.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      row: The row resulting from the query.

    Yields:
      An event object (instance of FirefoxCookieEvent) containing the event
      data.
    """
    if row['creationTime']:
      yield FirefoxCookieEvent(
          row['creationTime'], eventdata.EventTimestamp.CREATION_TIME,
          row['host'], row['name'], row['value'], row['path'], row['isSecure'],
          row['isHttpOnly'])

    if row['lastAccessed']:
      yield FirefoxCookieEvent(
          row['lastAccessed'], eventdata.EventTimestamp.ACCESS_TIME,
          row['host'], row['name'], row['value'], row['path'], row['isSecure'],
          row['isHttpOnly'])

    if row['expiry']:
      # Expiry time (nsCookieService::GetExpiry in
      # netwerk/cookie/nsCookieService.cpp).
      # It's calculeated as the difference between the server time and the time
      # the server wants the cookie to expire and adding that difference to the
      # client time. This localizes the client time regardless of whether or not
      # the TZ environment variable was set on the client.
      timestamp = timelib.Timestamp.FromPosixTime(row['expiry'])
      yield FirefoxCookieEvent(
          timestamp, u'Cookie Expires', row['host'], row['name'], row['value'],
          row['path'], row['isSecure'], row['isHttpOnly'])

    # Go through all cookie plugins to see if there are is any specific parsing
    # needed.
    hostname = row['host']
    if hostname.startswith('.'):
      hostname = hostname[1:]
    url = u'http{0:s}://{1:s}{2:s}'.format(
        u's' if row['isSecure'] else u'', hostname, row['path'])
    for cookie_plugin in self._cookie_plugins:
      try:
        for event_object in cookie_plugin.Process(
            parser_context, cookie_name=row['name'], cookie_data=row['value'],
            url=url):
          event_object.plugin = cookie_plugin.plugin_name
          yield event_object
      except errors.WrongPlugin:
        pass
