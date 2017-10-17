# -*- coding: utf-8 -*-
"""The Google Analytics cookie event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AnalyticsUtmaCookieFormatter(interface.ConditionalEventFormatter):
  """The UTMA Google Analytics cookie event formatter."""

  DATA_TYPE = 'cookie:google:analytics:utma'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})',
      'Sessions: {sessions}',
      'Domain Hash: {domain_hash}',
      'Visitor ID: {visitor_id}']

  FORMAT_STRING_SHORT_PIECES = [
      '{url}',
      '({cookie_name})']

  SOURCE_LONG = 'Google Analytics Cookies'
  SOURCE_SHORT = 'WEBHIST'


class AnalyticsUtmbCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The UTMB Google Analytics cookie event formatter."""

  DATA_TYPE = 'cookie:google:analytics:utmb'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})',
      'Pages Viewed: {pages_viewed}',
      'Domain Hash: {domain_hash}']


class AnalyticsUtmtCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The UTMT Google Analytics cookie event formatter."""

  DATA_TYPE = 'cookie:google:analytics:utmt'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})']


class AnalyticsUtmzCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The UTMZ Google Analytics cookie event formatter."""

  DATA_TYPE = 'cookie:google:analytics:utmz'

  FORMAT_STRING_PIECES = [
      '{url}',
      '({cookie_name})',
      'Sessions: {sessions}',
      'Domain Hash: {domain_hash}',
      'Sources: {sources}',
      'Last source used to access: {utmcsr}',
      'Ad campaign information: {utmccn}',
      'Last type of visit: {utmcmd}',
      'Keywords used to find site: {utmctr}',
      'Path to the page of referring link: {utmcct}']


manager.FormattersManager.RegisterFormatters([
    AnalyticsUtmaCookieFormatter, AnalyticsUtmbCookieFormatter,
    AnalyticsUtmtCookieFormatter, AnalyticsUtmzCookieFormatter])
