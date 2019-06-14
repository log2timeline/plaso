# -*- coding: utf-8 -*-
"""Twitter on iOS 8+ database formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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

  _FOLLOWING = {
      0: 'No',
      1: 'Yes',
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    following = event_values.get('following', None)
    if following is not None:
      event_values['following'] = (
          self._FOLLOWING.get(following, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


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

  _FAVORITED = {
      0: 'No',
      1: 'Yes',
  }

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    favorited = event_values.get('favorited', None)
    if favorited is not None:
      event_values['favorited'] = (
          self._FAVORITED.get(favorited, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    TwitterIOSContactFormatter, TwitterIOSStatusFormatter])
