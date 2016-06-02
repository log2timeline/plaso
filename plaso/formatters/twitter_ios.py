# -*- coding: utf-8 -*-
"""Twitter on iOS 8+ database formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class TwitterIOSContactFormatter(interface.ConditionalEventFormatter):
  """Parent class for Twitter on iOS 8+ contacts formatters."""

  FORMAT_STRING_PIECES = [
      u'Screen name: {screen_name}',
      u'Profile picture URL: {profile_url}',
      u'Name: {name}',
      u'Location: {location}',
      u'Description: {description}',
      u'URL: {url}',
      u'Following: {following}',
      u'Number of followers: {followers_cnt}',
      u'Number of following: {following_cnt}',
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

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    following = event_values.get(u'following', None)
    if following is not None:
      event_values[u'following'] = (
          self._FOLLOWING.get(following, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


class TwitterIOSContactCreationFormatter(TwitterIOSContactFormatter):
  """Formatter for Twitter on iOS 8+ contacts creation event."""
  DATA_TYPE = u'twitter:ios:contact_creation'


class TwitterIOSContactUpdateFormatter(TwitterIOSContactFormatter):
  """Formatter for Twitter on iOS 8+ contacts update event."""
  DATA_TYPE = u'twitter:ios:contact_update'


class TwitterIOSStatusFormatter(interface.ConditionalEventFormatter):
  """Parent class for Twitter on iOS 8+ status formatters."""

  FORMAT_STRING_PIECES = [
      u'Name: {name}',
      u'User Id: {user_id}',
      u'Message: {text}',
      u'Favorite: {favorited}',
      u'Retweet Count: {retweet_cnt}',
      u'Favorite Count: {favorite_cnt}',
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

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.CopyToDict()

    favorited = event_values.get(u'favorited', None)
    if favorited is not None:
      event_values[u'favorited'] = (
          self._FAVORITED.get(favorited, u'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


class TwitterIOSStatusCreationFormatter(TwitterIOSStatusFormatter):
  """Formatter for Twitter on iOS 8+ status creation event."""
  DATA_TYPE = u'twitter:ios:status_creation'


class TwitterIOSStatusUpdateFormatter(TwitterIOSStatusFormatter):
  """Formatter for Twitter on iOS 8+ status update event."""
  DATA_TYPE = u'twitter:ios:status_update'


manager.FormattersManager.RegisterFormatters([
    TwitterIOSContactCreationFormatter, TwitterIOSContactUpdateFormatter,
    TwitterIOSStatusCreationFormatter, TwitterIOSStatusUpdateFormatter])
