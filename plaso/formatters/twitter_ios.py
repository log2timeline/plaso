# -*- coding: utf-8 -*-
"""Twitter on iOS 8+ database formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class TwitterIOSContactFormatter(interface.ConditionalEventFormatter):
  """Twitter on iOS 8+ contact event formatter."""

  DATA_TYPE = u'twitter:ios:contact'

  FORMAT_STRING_PIECES = [
      u'Screen name: {screen_name}',
      u'Profile picture URL: {profile_url}',
      u'Name: {name}',
      u'Location: {location}',
      u'Description: {description}',
      u'URL: {url}',
      u'Following: {following}',
      u'Number of followers: {followers_count}',
      u'Number of following: {following_count}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      u'Screen name: {screen_name}',
      u'Description: {description}',
      u'URL: {url}',
  ]

  SOURCE_LONG = u'Twitter iOS Contacts'
  SOURCE_SHORT = u'Twitter iOS'

  _FOLLOWING = {
      0: u'No',
      1: u'Yes',
  }

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    following = event_values.get(u'following', None)
    if following is not None:
      event_values[u'following'] = (
          self._FOLLOWING.get(following, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


class TwitterIOSStatusFormatter(interface.ConditionalEventFormatter):
  """Twitter on iOS 8+ status event formatter."""

  DATA_TYPE = u'twitter:ios:status'

  FORMAT_STRING_PIECES = [
      u'Name: {name}',
      u'User Id: {user_id}',
      u'Message: {text}',
      u'Favorite: {favorited}',
      u'Retweet Count: {retweet_count}',
      u'Favorite Count: {favorite_count}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      u'Name: {name}',
      u'Message: {text}',
  ]

  SOURCE_LONG = u'Twitter iOS Status'
  SOURCE_SHORT = u'Twitter iOS'

  _FAVORITED = {
      0: u'No',
      1: u'Yes',
  }

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    favorited = event_values.get(u'favorited', None)
    if favorited is not None:
      event_values[u'favorited'] = (
          self._FAVORITED.get(favorited, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    TwitterIOSContactFormatter, TwitterIOSStatusFormatter])
