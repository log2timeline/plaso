# -*- coding:utf-8 -*-
"""Parser for Twitter on iOS 8+ database.

   SQLite database path:
   /private/var/mobile/Containers/Data/Application/Library/Caches/databases/
   SQLite database name:
   twitter.db
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class TwitterIOSContactEvent(time_events.PosixTimeEvent):
  """Parent class for Twitter on iOS 8+ contacts events.

  Attributes:
    screen_name: Contact's screen name.
    name: Contact's profile name.
    profile_url: Contact's  profile picture url.
    location: Contact's profile location.
    url: Contact's profile url.
    description: Contact's profile description.
    following: Variable to describe if the contact is following the account.
    following_cnt: The number of following.
    followers_cnt: The number of followers.
  """

  def __init__(
      self, posix_time, posix_time_description, screen_name, name, profile_url,
      location, url, description, following, following_cnt, followers_cnt):
    """Initalizes a TwitterIOSContacts event.

    Args:
      posix_time: The POSIX time value.
      posix_time_description: The description of the usage of the timestamp.
      screen_name: Contact's screen name.
      name: Contact's profile name.
      profile_url: Contact's  profile picture url.
      location: Contact's profile location.
      url: Contact's profile url.
      description: Contact's profile description.
      following: Variable to describe if the contact is following the account.
      following_cnt: The number of following.
      followers_cnt: The number of followers.
    """
    super(TwitterIOSContactEvent, self).__init__(
        posix_time, posix_time_description)
    self.screen_name = screen_name
    self.name = name
    self.profile_url = profile_url
    self.location = location
    self.url = url
    self.description = description
    self.following = following
    self.following_cnt = following_cnt
    self.followers_cnt = followers_cnt


class TwitterIOSContactCreationEvent(TwitterIOSContactEvent):
  """Convenience class for Twitter contacts creation events."""
  DATA_TYPE = u'twitter:ios:contact_creation'


class TwitterIOSContactUpdateEvent(TwitterIOSContactEvent):
  """Convenience class for Twitter contacts update events."""
  DATA_TYPE = u'twitter:ios:contact_update'


class TwitterIOSStatusEvent(time_events.PosixTimeEvent):
  """Parent class for Twitter on iOS 8+ status events.

  Attributes:
    posix_time: The POSIX time value.
    text: The content of the status messsage.
    user_id: User unique identifier.
    name: User's profile name.
    retweet_cnt: Number of times the status has been retweeted.
    favorite_cnt: Number of times the status has been favorited.
    favorited: Variable to mark status as favorite by the account.
  """

  def __init__(
      self, posix_time, posix_time_description, text, user_id, name,
      retweet_cnt, favorite_cnt, favorited):
    """Initalizes a TwitterIOSStatuses event.

    Args:
      posix_time: The POSIX time value.
      posix_time_description: The description of the usage of the timestamp.
      text: The content of the status messsage.
      user_id: User unique identifier.
      name: User's profile name.
      retweet_cnt: Number of times the status has been retweeted.
      favorite_cnt: Number of times the status has been favorited.
      favorited: Variable to mark status as favorite by the account.
    """
    super(TwitterIOSStatusEvent, self).__init__(
        posix_time, posix_time_description)
    self.text = text
    self.user_id = user_id
    self.name = name
    self.retweet_cnt = retweet_cnt
    self.favorite_cnt = favorite_cnt
    self.favorited = favorited


class TwitterIOSStatusCreationEvent(TwitterIOSStatusEvent):
  """Convenience class for Twitter status creation events."""
  DATA_TYPE = u'twitter:ios:status_creation'


class TwitterIOSStatusUpdateEvent(TwitterIOSStatusEvent):
  """Convenience class for Twitter status update events."""
  DATA_TYPE = u'twitter:ios:status_update'


class TwitterIOSPlugin(interface.SQLitePlugin):
  """Parser for Twitter on iOS 8+ database."""

  # twitter_ios or just twitter?
  NAME = u'twitter_ios'
  DESCRIPTION = u'Parser for Twitter on iOS 8+ database'

  # frozenset?
  QUERIES = [
      ((u'SELECT createdDate, updatedAt, screenName, name, profileImageUrl,'
        u'location, description, url, following, followersCount, followingCount'
        u' FROM Users ORDER BY createdDate'), u'ParseContactRow'),
      ((u'SELECT Statuses.date AS date, Statuses.text AS text, Statuses.userId '
        u'AS user_id, Users.name AS name, Statuses.retweetCount AS '
        u'retweetCount, Statuses.favoriteCount AS favoriteCount, '
        u'Statuses.favorited AS favorited, Statuses.updatedAt AS updatedAt '
        u'FROM Statuses LEFT join Users ON Statuses.userId = Users.id ORDER '
        u'BY date'), u'ParseStatusRow')]

  REQUIRED_TABLES = frozenset([u'Lists', u'MyRetweets', u'StatusesShadow',
                               u'UsersShadow', u'ListsShadow', u'Statuses',
                               u'Users'])

  def ParseContactRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """

    if row['createdDate'] is not None:
      event_object = TwitterIOSContactCreationEvent(
          row['createdDate'], eventdata.EventTimestamp.CREATION_TIME,
          row['screenName'], row['name'], row['profileImageUrl'],
          row['location'], row['url'], row['description'], row['following'],
          row['followingCount'], row['followersCount'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['updatedAt'] is not None:
      event_object = TwitterIOSContactUpdateEvent(
          row['updatedAt'], eventdata.EventTimestamp.UPDATE_TIME,
          row['screenName'], row['name'], row['profileImageUrl'],
          row['location'], row['url'], row['description'], row['following'],
          row['followingCount'], row['followersCount'])
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseStatusRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """

    if row['date'] is not None:
      event_object = TwitterIOSStatusCreationEvent(
          row['date'], eventdata.EventTimestamp.CREATION_TIME, row['text'],
          row['user_id'], row['name'], row['retweetCount'],
          row['favoriteCount'], row['favorited'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['updatedAt'] is not None:
      event_object = TwitterIOSStatusUpdateEvent(
          row['updatedAt'], eventdata.EventTimestamp.UPDATE_TIME, row['text'],
          row['user_id'], row['name'], row['retweetCount'],
          row['favoriteCount'], row['favorited'])
      parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(TwitterIOSPlugin)
