# -*- coding:utf-8 -*-
"""Parser for Twitter on iOS 8+ database.

SQLite database path:
/private/var/mobile/Containers/Data/Application/Library/Caches/databases/
SQLite database name: twitter.db
"""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class TwitterIOSContactEvent(time_events.PosixTimeEvent):
  """Parent class for Twitter on iOS 8+ contacts events.

  Attributes:
    description: A string containing the contact's profile description.
    followers_cnt: An integer containing the number of followers.
    following: An integer value to describe if the contact is following the
               user's account, represented by 0 or 1.
    following_cnt: An integer containing the number of following.
    location: A string containing the contact's profile location.
    name: A string containing the contact's profile name.
    profile_url: A string containing the contact's  profile picture URL.
    screen_name: A string containing the contact's screen name.
    url: A string containing the contact's profile URL.
  """

  def __init__(
      self, posix_time, posix_time_description, screen_name, name, profile_url,
      location, url, description, following, following_cnt, followers_cnt):
    """Initalizes a TwitterIOSContacts event.

    Args:
      posix_time: The POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      posix_time_description: The description of the usage of the timestamp.
      screen_name: A string containing the contact's screen name.
      name: A string containing the contact's profile name.
      profile_url: A string containing the contact's  profile picture URL.
      location: A string containing the contact's profile location.
      url: A string containing the contact's profile URL.
      description: A string containing the contact's profile description.
      following: An interger value to describe if the contact is following the
                 user's account, represented by 0 or 1.
      following_cnt: An integer containing the number of following.
      followers_cnt: An integer containing the number of followers.
    """
    super(TwitterIOSContactEvent, self).__init__(
        posix_time, posix_time_description)
    self.description = description
    self.followers_cnt = followers_cnt
    self.following = following
    self.following_cnt = following_cnt
    self.location = location
    self.name = name
    self.profile_url = profile_url
    self.screen_name = screen_name
    self.url = url


class TwitterIOSContactCreationEvent(TwitterIOSContactEvent):
  """Convenience class for Twitter contacts creation events."""
  DATA_TYPE = u'twitter:ios:contact_creation'


class TwitterIOSContactUpdateEvent(TwitterIOSContactEvent):
  """Convenience class for Twitter contacts update events."""
  DATA_TYPE = u'twitter:ios:contact_update'


class TwitterIOSStatusEvent(time_events.PosixTimeEvent):
  """Parent class for Twitter on iOS 8+ status events.

  Attributes:
    favorite_cnt: An integer containing the number of times the status message
                  has been favorited.
    favorited: An integer value to mark status as favorite by the account.
    name: A string containing the user's profile name.
    retweet_cnt: A string containing the number of times the status message has
                 been retweeted.
    text: A string containing the content of the status messsage.
    user_id: An integer containing the user unique identifier.
  """

  def __init__(
      self, posix_time, posix_time_description, text, user_id, name,
      retweet_cnt, favorite_cnt, favorited):
    """Initalizes a TwitterIOSStatuses event.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      posix_time_description: The description of the usage of the timestamp.
      text: A string containing the content of the status messsage.
      user_id: An integer containing the user unique identifier.
      name: A string containing the user's profile name.
      retweet_cnt: A string containing the number of times the status message
                   has been retweeted.
      favorite_cnt: An integer containing the number of times the status
                    message has been favorited.
      favorited: An integer value to mark status as favorite by the account.
    """
    super(TwitterIOSStatusEvent, self).__init__(
        posix_time, posix_time_description)
    self.favorite_cnt = favorite_cnt
    self.favorited = favorited
    self.name = name
    self.retweet_cnt = retweet_cnt
    self.text = text
    self.user_id = user_id


class TwitterIOSStatusCreationEvent(TwitterIOSStatusEvent):
  """Convenience class for Twitter status creation events."""
  DATA_TYPE = u'twitter:ios:status_creation'


class TwitterIOSStatusUpdateEvent(TwitterIOSStatusEvent):
  """Convenience class for Twitter status update events."""
  DATA_TYPE = u'twitter:ios:status_update'


class TwitterIOSPlugin(interface.SQLitePlugin):
  """Parser for Twitter on iOS 8+ database."""

  NAME = u'twitter_ios'
  DESCRIPTION = u'Parser for Twitter on iOS 8+ database'

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

  REQUIRED_TABLES = frozenset([
      u'Lists', u'MyRetweets', u'StatusesShadow', u'UsersShadow',
      u'ListsShadow', u'Statuses', u'Users'])

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
