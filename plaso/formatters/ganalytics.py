# -*- coding: utf-8 -*-
"""The Google Analytics cookie event formatters."""

from plaso.formatters import interface
from plaso.formatters import manager


class AnalyticsUtmaCookieFormatter(interface.ConditionalEventFormatter):
  """The UTMA Google Analytics cookie event formatter."""

  DATA_TYPE = u'cookie:google:analytics:utma'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Sessions: {sessions}',
      u'Domain Hash: {domain_hash}',
      u'Visitor ID: {visitor_id}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({cookie_name})']

  SOURCE_LONG = u'Google Analytics Cookies'
  SOURCE_SHORT = u'WEBHIST'


class AnalyticsUtmbCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The UTMB Google Analytics cookie event formatter."""

  DATA_TYPE = u'cookie:google:analytics:utmb'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Pages Viewed: {pages_viewed}',
      u'Domain Hash: {domain_hash}']


class AnalyticsUtmzCookieFormatter(AnalyticsUtmaCookieFormatter):
  """The UTMZ Google Analytics cookie event formatter."""

  DATA_TYPE = u'cookie:google:analytics:utmz'

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
