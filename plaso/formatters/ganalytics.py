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
"""This file contains a formatter for the Google Analytics cookie."""

from plaso.formatters import interface
from plaso.formatters import manager


class AnalyticsUtmaCookieFormatter(interface.ConditionalEventFormatter):
  """The event formatter for UTMA Google Analytics cookie."""

  DATA_TYPE = 'cookie:google:analytics:utma'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Sessions: {sessions}',
      u'Domain Hash: {domain_hash}',
      u'Visitor ID: {domain_hash}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({cookie_name})']

  SOURCE_LONG = 'Google Analytics Cookies'
  SOURCE_SHORT = 'WEBHIST'


class AnalyticsUtmbCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The event formatter for UTMB Google Analytics cookie."""

  DATA_TYPE = 'cookie:google:analytics:utmb'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Pages Viewed: {pages_viewed}',
      u'Domain Hash: {domain_hash}']


class AnalyticsUtmzCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The event formatter for UTMZ Google Analytics cookie."""

  DATA_TYPE = 'cookie:google:analytics:utmz'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Sessions: {sessions}',
      u'Domain Hash: {domain_hash}',
      u'Sources: {sources}',
      u'Last source used to access: {utmcsr}',
      u'Ad campaign information: {utmccn}',
      u'Last type of visit: {utmcmd}',
      u'Keywords used to find site: {utmctr}',
      u'Path to the page of referring link: {utmcct}']


manager.FormattersManager.RegisterFormatters([
    AnalyticsUtmaCookieFormatter, AnalyticsUtmbCookieFormatter,
    AnalyticsUtmzCookieFormatter])
