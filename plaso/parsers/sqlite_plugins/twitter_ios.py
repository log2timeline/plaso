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

  SCHEMAS = [
      {u'Lists':
       u'CREATE TABLE Lists ( \'id\' INTEGER PRIMARY KEY, \'name\' TEXT, '
       u'\'slug\' TEXT, \'desc\' TEXT, \'private\' INTEGER, '
       u'\'subscriberCount\' INTEGER, \'memberCount\' INTEGER, \'userId\' '
       u'INTEGER, \'updatedAt\' REAL )',
       u'ListsShadow':
       u'CREATE TABLE ListsShadow ( \'id\' INTEGER PRIMARY KEY, \'name\' '
       u'TEXT, \'slug\' TEXT, \'desc\' TEXT, \'private\' INTEGER, '
       u'\'subscriberCount\' INTEGER, \'memberCount\' INTEGER, \'userId\' '
       u'INTEGER, \'updatedAt\' REAL )',
       u'MyRetweets':
       u'CREATE TABLE MyRetweets ( \'statusId\' INTEGER PRIMARY KEY, '
       u'\'myRetweetId\' INTEGER )',
       u'Statuses':
       u'CREATE TABLE Statuses ( \'id\' INTEGER PRIMARY KEY, \'text\' TEXT, '
       u'\'date\' REAL, \'userId\' INTEGER, \'inReplyToStatusId\' INTEGER, '
       u'\'retweetedStatusId\' INTEGER, \'geotag\' BLOB, \'entities\' BLOB, '
       u'\'card\' BLOB, \'cardUsers\' BLOB, \'primaryCardType\' INTEGER, '
       u'\'cardVersion\' INTEGER, \'retweetCount\' INTEGER, '
       u'\'favoriteCount\' INTEGER, \'favorited\' INTEGER, \'updatedAt\' '
       u'REAL, \'extraScribeItem\' BLOB, \'withheldScope\' TEXT, '
       u'\'withheldInCountries\' TEXT, \'inReplyToUsername\' TEXT, '
       u'\'possiblySensitive\' INTEGER, \'isPossiblySensitiveAppealable\' '
       u'INTEGER, \'isLifelineAlert\' INTEGER, \'isTruncated\' INTEGER, '
       u'\'previewLength\' INTEGER, \'fullTextLength\' INTEGER, \'lang\' '
       u'TEXT, \'supplmentalLanguage\' TEXT, \'includeInProfileTimeline\' '
       u'INTEGER, \'quotedStatusId\' INTEGER, \'source\' TEXT )',
       u'StatusesShadow':
       u'CREATE TABLE StatusesShadow ( \'id\' INTEGER PRIMARY KEY, \'text\' '
       u'TEXT, \'date\' REAL, \'userId\' INTEGER, \'inReplyToStatusId\' '
       u'INTEGER, \'retweetedStatusId\' INTEGER, \'geotag\' BLOB, '
       u'\'entities\' BLOB, \'card\' BLOB, \'cardUsers\' BLOB, '
       u'\'primaryCardType\' INTEGER, \'cardVersion\' INTEGER, '
       u'\'retweetCount\' INTEGER, \'favoriteCount\' INTEGER, \'favorited\' '
       u'INTEGER, \'updatedAt\' REAL, \'extraScribeItem\' BLOB, '
       u'\'withheldScope\' TEXT, \'withheldInCountries\' TEXT, '
       u'\'inReplyToUsername\' TEXT, \'possiblySensitive\' INTEGER, '
       u'\'isPossiblySensitiveAppealable\' INTEGER, \'isLifelineAlert\' '
       u'INTEGER, \'isTruncated\' INTEGER, \'previewLength\' INTEGER, '
       u'\'fullTextLength\' INTEGER, \'lang\' TEXT, \'supplementalLanguage\' '
       u'TEXT, \'includeInProfileTimeline\' INTEGER, \'quotedStatusId\' '
       u'INTEGER, \'source\' TEXT )',
       u'Users':
       u'CREATE TABLE Users ( \'id\' INTEGER PRIMARY KEY, \'screenName\' '
       u'TEXT COLLATE NOCASE, \'profileImageUrl\' TEXT, \'profileBannerUrl\' '
       u'TEXT, \'profileLinkColorHexTriplet\' INTEGER, \'name\' TEXT, '
       u'\'location\' TEXT, \'structuredLocation\' BLOB, \'description\' '
       u'TEXT, \'url\' TEXT, \'urlEntities\' BLOB, \'bioEntities\' BLOB, '
       u'\'protected\' INTEGER, \'verified\' INTEGER, \'following\' INTEGER, '
       u'\'deviceFollowing\' INTEGER, \'advertiserAccountType\' INTEGER, '
       u'\'statusesCount\' INTEGER, \'mediaCount\' INTEGER, '
       u'\'favoritesCount\' INTEGER, \'followingCount\' INTEGER, '
       u'\'followersCount\' INTEGER, \'followersCountFast\' INTEGER, '
       u'\'followersCountNormal\' INTEGER, \'couldBeStale\' INTEGER, '
       u'\'isLifelineInstitution\' INTEGER, \'hasCollections\' INTEGER, '
       u'\'updatedAt\' REAL, \'createdDate\' REAL, \'isTranslator\' INTEGER, '
       u'\'hasExtendedProfileFields\' INTEGER, \'extendedProfileFields\' '
       u'BLOB, \'pinnedTweetId\' INTEGER, \'businessProfileState\' INTEGER, '
       u'\'analyticsType\' INTEGER )',
       u'UsersShadow':
       u'CREATE TABLE UsersShadow ( \'id\' INTEGER PRIMARY KEY, '
       u'\'screenName\' TEXT COLLATE NOCASE, \'profileImageUrl\' TEXT, '
       u'\'profileBannerUrl\' TEXT, \'profileLinkColorHexTriplet\' INTEGER, '
       u'\'name\' TEXT, \'location\' TEXT, \'structuredLocation\' BLOB, '
       u'\'description\' TEXT, \'url\' TEXT, \'urlEntities\' BLOB, '
       u'\'bioEntities\' BLOB, \'protected\' INTEGER, \'verified\' INTEGER, '
       u'\'following\' INTEGER, \'deviceFollowing\' INTEGER, '
       u'\'advertiserAccountType\' INTEGER, \'statusesCount\' INTEGER, '
       u'\'mediaCount\' INTEGER, \'favoritesCount\' INTEGER, '
       u'\'followingCount\' INTEGER, \'followersCount\' INTEGER, '
       u'\'followersCountFast\' INTEGER, \'followersCountNormal\' INTEGER, '
       u'\'couldBeStale\' INTEGER, \'isLifelineInstitution\' INTEGER, '
       u'\'hasCollections\' INTEGER, \'updatedAt\' REAL, \'createdDate\' '
       u'REAL, \'isTranslator\' INTEGER, \'hasExtendedProfileFields\' '
       u'INTEGER, \'extendedProfileFields\' BLOB, \'pinnedTweetId\' INTEGER, '
       u'\'businessProfileState\' INTEGER, \'analyticsType\' INTEGER )'}]

  def ParseContactRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
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
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
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
