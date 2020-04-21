# -*- coding: utf-8 -*-
"""The Google Chrome extension activity database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeExtensionActivityEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome extension activity event."""

  DATA_TYPE = 'chrome:extension_activity:activity_log'

  FORMAT_STRING_PIECES = [
      'Chrome extension: {extension_id}',
      'Action type: {action_type_string}',
      '(type {action_type})',
      'Activity identifier: {activity_id}',
      'Page URL: {page_url}',
      'Page title: {page_title}',
      'API name: {api_name}',
      'Args: {args}',
      'Other: {other}']

  FORMAT_STRING_SHORT_PIECES = [
      '{extension_id}',
      '{api_name}',
      '{args}']

  SOURCE_LONG = 'Chrome Extension Activity'
  SOURCE_SHORT = 'WEBHIST'

  # From:
  # https://chromium.googlesource.com/chromium/src.git/+/master/chrome/browser/extensions/activity_log/activity_actions.h
  _CHROME_ACTION_TYPES = {
      0 : 'API call',
      1 : 'API event callback',
      2 : 'API action blocked',
      3 : 'Content Script inserted',
      4 : 'DOM access',
      5 : 'DOM event',
      6 : 'WebRequest',
      1001 : 'Unspecified'
  }

  def __init__(self):
    """Initializes a Chrome extension activity format helper."""
    super(ChromeExtensionActivityEventFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='unknown', input_attribute='action_type',
        output_attribute='action_type_string', values=self._CHROME_ACTION_TYPES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(
    ChromeExtensionActivityEventFormatter)
