# -*- coding: utf-8 -*-
"""Twitter on Android database formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TwitterAndroidStatusFormatter(interface.ConditionalEventFormatter):
  """Twitter for Android status event formatter."""

  DATA_TYPE = 'twitter:android:status'

  FORMAT_STRING_PIECES = [
      'User: {username}',
      'Status: {content}',
      'Favorited: {favorited}',
      'Retweeted: {retweeted}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'User: {username}',
      'Status: {content}'
  ]

  SOURCE_LONG = 'Twitter Android Status'
  SOURCE_SHORT = 'Twitter Android'

  _YES_NO_VALUES = {
      0: 'No',
      1: 'Yes'
  }

  def __init__(self):
    """Initializes a Twitter for Android status event format helper."""
    super(TwitterAndroidStatusFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='favorited',
        output_attribute='favorited', values=self._YES_NO_VALUES)

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='retweeted',
        output_attribute='retweeted', values=self._YES_NO_VALUES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(TwitterAndroidStatusFormatter)
