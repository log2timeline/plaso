# -*- coding: utf-8 -*-
"""The Google Chrome extension activity database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeExtensionActivityEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension activity event."""

  DATA_TYPE = u'chrome:extension_activity:activity_log'

  FORMAT_STRING_PIECES = [
      u'Chrome extension: {extension_id}',
      u'Action type: {action_type}',
      u'Activity identifier: {activity_id}',
      u'Page URL: {page_url}',
      u'Page title: {page_title}',
      u'API name: {api_name}',
      u'Args: {args}',
      u'Other: {other}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{api_name}',
      u'{args}']

  SOURCE_LONG = u'Chrome Extension Activity'
  SOURCE_SHORT = u'WEBHIST'

  # TODO: add action_type string representation.


manager.FormattersManager.RegisterFormatter(
    ChromeExtensionActivityEventFormatter)
