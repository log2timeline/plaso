# -*- coding: utf-8 -*-
"""Twitter on android database formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


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
  """Twitter for android status event formatter."""

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

  _BOOLEAN_PRETTY_PRINT = {
      0: 'No',
      1: 'Yes'
  }

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event):
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
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event.data_type))

    event_values = event.CopyToDict()

    favorited = event_values.get('favorited', None)
    if favorited is not None:
      event_values['favorited'] = (
          self._BOOLEAN_PRETTY_PRINT.get(favorited, 'UNKNOWN'))

    retweeted = event_values.get('retweeted', None)
    if retweeted is not None:
      event_values['retweeted'] = (
          self._BOOLEAN_PRETTY_PRINT.get(retweeted, 'UNKNOWN'))

    return self._ConditionalFormatMessages(event_values)


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
