# -*- coding: utf-8 -*-
"""The Google Chrome Preferences file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeContentSettingsExceptionsFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Chrome content_settings exceptions event."""

  DATA_TYPE = 'chrome:preferences:content_settings:exceptions'

  FORMAT_STRING_PIECES = [
      'Permission {permission}',
      'used by {subject}']

  FORMAT_STRING_SHORT_PIECES = [
      'Permission {permission}',
      'used by {subject}']

  def FormatEventValues(self, event_values):
    """Formats event values using the helpers.

    Args:
      event_values (dict[str, object]): event values.
    """
    primary_url = event_values['primary_url']
    secondary_url = event_values['secondary_url']

    # There is apparently a bug, either in GURL.cc or
    # content_settings_pattern.cc where URLs with file:// scheme are stored in
    # the URL as an empty string, which is later detected as being Invalid, and
    # Chrome produces the following example logs:
    # content_settings_pref.cc(469)] Invalid pattern strings: https://a.com:443,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,*
    # More research needed, could be related to https://crbug.com/132659

    if primary_url == '':
      subject = 'local file'

    elif secondary_url in (primary_url, '*'):
      subject = primary_url

    elif secondary_url == '':
      subject = '{0:s} embedded in local file'.format(primary_url)

    else:
      subject = '{0:s} embedded in {1:s}'.format(primary_url, secondary_url)

    event_values['subject'] = subject


manager.FormattersManager.RegisterFormatter(
    ChromeContentSettingsExceptionsFormatter)
