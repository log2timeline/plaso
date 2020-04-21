# -*- coding: utf-8 -*-
"""Twitter on Android database formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TwitterAndroidContactFormatter(interface.ConditionalEventFormatter):
  """Twitter for android contact event formatter."""

  DATA_TYPE = 'twitter:android:contact'

  FORMAT_STRING_PIECES = [
      'Screen name: {username}',
      'Profile picture URL: {image_url}',
      'Name: {name}',
      'Location: {location}',
      'Description: {description}',
      'URL: {web_url}',
      'Number of followers: {followers}',
      'Number of following: {friend}',
      'Number of tweets: {statuses}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'Screen name: {username}',
      'Description: {description}',
      'URL: {web_url}',
  ]

  SOURCE_LONG = 'Twitter Android Contacts'
  SOURCE_SHORT = 'Twitter Android'


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


class TwitterAndroidSearchFormatter(interface.ConditionalEventFormatter):
  """Twitter for android search event formatter."""

  DATA_TYPE = 'twitter:android:search'

  FORMAT_STRING_PIECES = [
      'Name: {name}',
      'Query: {search_query}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'Query: {search_query}'
  ]

  SOURCE_LONG = 'Twitter Android Search'
  SOURCE_SHORT = 'Twitter Android'


manager.FormattersManager.RegisterFormatters([
    TwitterAndroidContactFormatter, TwitterAndroidStatusFormatter,
    TwitterAndroidSearchFormatter])
