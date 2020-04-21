# -*- coding: utf-8 -*-
"""Twitter on iOS 8+ database formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class TwitterIOSContactFormatter(interface.ConditionalEventFormatter):
  """Twitter on iOS 8+ contact event formatter."""

  DATA_TYPE = 'twitter:ios:contact'

  FORMAT_STRING_PIECES = [
      'Screen name: {screen_name}',
      'Profile picture URL: {profile_url}',
      'Name: {name}',
      'Location: {location}',
      'Description: {description}',
      'URL: {url}',
      'Following: {following}',
      'Number of followers: {followers_count}',
      'Number of following: {following_count}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'Screen name: {screen_name}',
      'Description: {description}',
      'URL: {url}',
  ]

  SOURCE_LONG = 'Twitter iOS Contacts'
  SOURCE_SHORT = 'Twitter iOS'

  _YES_NO_VALUES = {
      0: 'No',
      1: 'Yes',
  }

  def __init__(self):
    """Initializes a Twitter on iOS 8+ contact event format helper."""
    super(TwitterIOSContactFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='following',
        output_attribute='following', values=self._YES_NO_VALUES)

    self.helpers.append(helper)


class TwitterIOSStatusFormatter(interface.ConditionalEventFormatter):
  """Twitter on iOS 8+ status event formatter."""

  DATA_TYPE = 'twitter:ios:status'

  FORMAT_STRING_PIECES = [
      'Name: {name}',
      'User Id: {user_id}',
      'Message: {text}',
      'Favorite: {favorited}',
      'Retweet Count: {retweet_count}',
      'Favorite Count: {favorite_count}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      'Name: {name}',
      'Message: {text}',
  ]

  SOURCE_LONG = 'Twitter iOS Status'
  SOURCE_SHORT = 'Twitter iOS'

  _YES_NO_VALUES = {
      0: 'No',
      1: 'Yes',
  }

  def __init__(self):
    """Initializes a Twitter on iOS 8+ status event format helper."""
    super(TwitterIOSStatusFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='favorited',
        output_attribute='favorited', values=self._YES_NO_VALUES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatters([
    TwitterIOSContactFormatter, TwitterIOSStatusFormatter])
