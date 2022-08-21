# -*- coding: utf-8 -*-
"""Google Chrome preferences custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromePreferencesPrimaryURLFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Google Chrome preferences primary URL formatter helper."""

  IDENTIFIER = 'chrome_preferences_primary_url'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    primary_url = event_values.get('primary_url', None)
    if primary_url == '':
      event_values['primary_url'] = 'local file'


class ChromePreferencesSecondaryURLFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Google Chrome preferences secondary URL formatter helper."""

  IDENTIFIER = 'chrome_preferences_secondary_url'

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    # There appears to be an issue in either GURL.cc or
    # content_settings_pattern.cc where URLs with file:// scheme are stored in
    # the URL as an empty string, which is later detected as being Invalid, and
    # Chrome produces the following example logs:
    # content_settings_pref.cc(469)] Invalid pattern strings: https://a.com:443,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,
    # content_settings_pref.cc(295)] Invalid pattern strings: ,*
    # More research needed, could be related to https://crbug.com/132659

    primary_url = event_values.get('primary_url', None)
    secondary_url = event_values.get('secondary_url', None)
    if secondary_url == '':
      secondary_url = 'local file'

    if secondary_url in (primary_url, '*'):
      secondary_url = None

    event_values['secondary_url'] = secondary_url


manager.FormattersManager.RegisterEventFormatterHelpers([
    ChromePreferencesPrimaryURLFormatterHelper,
    ChromePreferencesSecondaryURLFormatterHelper])
