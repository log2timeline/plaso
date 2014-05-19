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
"""This file contains a formatter for the Google Chrome cookie."""

from plaso.lib import errors
from plaso.lib import eventdata


class ChromeCookieFormatter(eventdata.ConditionalEventFormatter):
  """The event formatter for cookie data in Chrome Cookies database."""

  DATA_TYPE = 'chrome:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Flags:',
      u'[HTTP only] = {httponly}',
      u'[Persistent] = {persistent}',
      u'(GA analysis: {ga_data})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{host}',
      u'({cookie_name})']

  SOURCE_LONG = 'Chrome Cookies'
  SOURCE_SHORT = 'WEBHIST'

  def GetMessages(self, event_object):
    """Format the message string."""
    if event_object.data_type != self.DATA_TYPE:
      raise errors.WrongFormatter(
          u'Unsupported data type: {0:s}.'.format(event_object.data_type))

    # TODO: Move this to a more generic GA cookie formatter once
    # more cookie parsers are implemented, since this should be a
    # shared code.
    # Create a separate cookie formatter that will handle them in a
    # generic sense and have this ineherit from that.
    ga_cookie = getattr(event_object, 'cookie_name', 'N/A')
    ga_data = []
    if ga_cookie == '__utmz':
      ga_data.append(u'Sessions: {}'.format(getattr(
          event_object, 'sessions', 0)))
      ga_data.append(u'Domain Hash: {}'.format(getattr(
          event_object, 'domain_hash', 'N/A')))
      ga_data.append(u'Sources: {}'.format(getattr(
          event_object, 'sources', 0)))
      ga_data.append(u'Variables: {}'.format(u' '.join(
          getattr(event_object, 'extra', []))))
    elif ga_cookie == '__utmb':
      ga_data.append(u'Pages Viewed: {}'.format(getattr(
          event_object, 'pages_viewed', 0)))
      ga_data.append(u'Domain Hash: {}'.format(getattr(
          event_object, 'domain_hash', 'N/A')))
    elif ga_cookie == '__utma':
      ga_data.append(u'Sessions: {}'.format(getattr(
          event_object, 'sessions', 0)))
      ga_data.append(u'Domain Hash: {}'.format(getattr(
          event_object, 'domain_hash', 'N/A')))
      ga_data.append(u'Visitor ID: {}'.format(getattr(
          event_object, 'domain_hash', 'N/A')))

    if ga_data:
      event_object.ga_data = u' - '.join(ga_data)

    return super(ChromeCookieFormatter, self).GetMessages(event_object)
