# -*- coding:utf-8 -*-
"""SQLite parser plugin for Twitter on iOS 8+ database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class TwitterIOSContactEventData(events.EventData):
  """Twitter on iOS 8+ contact event data.

  Attributes:
    description (str): description of the profile.
    followers_count (int): number of accounts following the contact.
    following_count (int): number of accounts the contact is following.
    following (int): 1 if the contact is following the user's account, 0 if not.
    location (str): location of the profile.
    name (str): name of the profile.
    profile_url (str): URL of the profile picture.
    query (str): SQL query that was used to obtain the event data.
    screen_name (str): screen name.
    url (str): URL of the profile.
  """

  DATA_TYPE = 'twitter:ios:contact'

  def __init__(self):
    """Initializes event data."""
    super(TwitterIOSContactEventData, self).__init__(data_type=self.DATA_TYPE)
    self.description = None
    self.followers_count = None
    self.following = None
    self.following_count = None
    self.location = None
    self.name = None
    self.profile_url = None
    self.query = None
    self.screen_name = None
    self.url = None


class TwitterIOSStatusEventData(events.EventData):
  """Parent class for Twitter on iOS 8+ status events.

  Attributes:
    favorite_count (int): number of times the status message has been favorited.
    favorited (int): value to mark status as favorite by the account.
    name (str): user's profile name.
    query (str): SQL query that was used to obtain the event data.
    retweet_count (str): number of times the status message has been retweeted.
    text (str): content of the status message.
    user_id (int): user unique identifier.
  """

  DATA_TYPE = 'twitter:ios:status'

  def __init__(self):
    """Initializes event data."""
    super(TwitterIOSStatusEventData, self).__init__(data_type=self.DATA_TYPE)
    self.favorite_count = None
    self.favorited = None
    self.name = None
    self.query = None
    self.retweet_count = None
    self.text = None
    self.user_id = None


class TwitterIOSPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Twitter on iOS 8+ database files.

  The Twitter on iOS 8+ database file is typically stored in:
  /private/var/mobile/Containers/Data/Application/Library/Caches/databases/
  twitter.db
  """

  NAME = 'twitter_ios'
  DATA_FORMAT = 'Twitter on iOS 8 and later SQLite database (twitter.db) file'

  REQUIRED_STRUCTURE = {
      'Users': frozenset([
          'createdDate', 'updatedAt', 'screenName', 'name', 'profileImageUrl',
          'location', 'description', 'url', 'following', 'followersCount',
          'followingCount', 'id']),
      'Statuses': frozenset([
          'date', 'text', 'userId', 'retweetCount', 'favoriteCount',
          'favorited', 'updatedAt'])}

  QUERIES = [
      (('SELECT createdDate, updatedAt, screenName, name, profileImageUrl,'
        'location, description, url, following, followersCount, followingCount'
        ' FROM Users ORDER BY createdDate'), 'ParseContactRow'),
      (('SELECT Statuses.date AS date, Statuses.text AS text, Statuses.userId '
        'AS user_id, Users.name AS name, Statuses.retweetCount AS '
        'retweetCount, Statuses.favoriteCount AS favoriteCount, '
        'Statuses.favorited AS favorited, Statuses.updatedAt AS updatedAt '
        'FROM Statuses LEFT join Users ON Statuses.userId = Users.id ORDER '
        'BY date'), 'ParseStatusRow')]

  SCHEMAS = [{
      'Lists': (
          'CREATE TABLE Lists ( \'id\' INTEGER PRIMARY KEY, \'name\' TEXT, '
          '\'slug\' TEXT, \'desc\' TEXT, \'private\' INTEGER, '
          '\'subscriberCount\' INTEGER, \'memberCount\' INTEGER, \'userId\' '
          'INTEGER, \'updatedAt\' REAL )'),
      'ListsShadow': (
          'CREATE TABLE ListsShadow ( \'id\' INTEGER PRIMARY KEY, \'name\' '
          'TEXT, \'slug\' TEXT, \'desc\' TEXT, \'private\' INTEGER, '
          '\'subscriberCount\' INTEGER, \'memberCount\' INTEGER, \'userId\' '
          'INTEGER, \'updatedAt\' REAL )'),
      'MyRetweets': (
          'CREATE TABLE MyRetweets ( \'statusId\' INTEGER PRIMARY KEY, '
          '\'myRetweetId\' INTEGER )'),
      'Statuses': (
          'CREATE TABLE Statuses ( \'id\' INTEGER PRIMARY KEY, \'text\' TEXT, '
          '\'date\' REAL, \'userId\' INTEGER, \'inReplyToStatusId\' INTEGER, '
          '\'retweetedStatusId\' INTEGER, \'geotag\' BLOB, \'entities\' BLOB, '
          '\'card\' BLOB, \'cardUsers\' BLOB, \'primaryCardType\' INTEGER, '
          '\'cardVersion\' INTEGER, \'retweetCount\' INTEGER, '
          '\'favoriteCount\' INTEGER, \'favorited\' INTEGER, \'updatedAt\' '
          'REAL, \'extraScribeItem\' BLOB, \'withheldScope\' TEXT, '
          '\'withheldInCountries\' TEXT, \'inReplyToUsername\' TEXT, '
          '\'possiblySensitive\' INTEGER, \'isPossiblySensitiveAppealable\' '
          'INTEGER, \'isLifelineAlert\' INTEGER, \'isTruncated\' INTEGER, '
          '\'previewLength\' INTEGER, \'fullTextLength\' INTEGER, \'lang\' '
          'TEXT, \'supplmentalLanguage\' TEXT, \'includeInProfileTimeline\' '
          'INTEGER, \'quotedStatusId\' INTEGER, \'source\' TEXT )'),
      'StatusesShadow': (
          'CREATE TABLE StatusesShadow ( \'id\' INTEGER PRIMARY KEY, \'text\' '
          'TEXT, \'date\' REAL, \'userId\' INTEGER, \'inReplyToStatusId\' '
          'INTEGER, \'retweetedStatusId\' INTEGER, \'geotag\' BLOB, '
          '\'entities\' BLOB, \'card\' BLOB, \'cardUsers\' BLOB, '
          '\'primaryCardType\' INTEGER, \'cardVersion\' INTEGER, '
          '\'retweetCount\' INTEGER, \'favoriteCount\' INTEGER, \'favorited\' '
          'INTEGER, \'updatedAt\' REAL, \'extraScribeItem\' BLOB, '
          '\'withheldScope\' TEXT, \'withheldInCountries\' TEXT, '
          '\'inReplyToUsername\' TEXT, \'possiblySensitive\' INTEGER, '
          '\'isPossiblySensitiveAppealable\' INTEGER, \'isLifelineAlert\' '
          'INTEGER, \'isTruncated\' INTEGER, \'previewLength\' INTEGER, '
          '\'fullTextLength\' INTEGER, \'lang\' TEXT, '
          '\'supplementalLanguage\' TEXT, \'includeInProfileTimeline\' '
          'INTEGER, \'quotedStatusId\' INTEGER, \'source\' TEXT )'),
      'Users': (
          'CREATE TABLE Users ( \'id\' INTEGER PRIMARY KEY, \'screenName\' '
          'TEXT COLLATE NOCASE, \'profileImageUrl\' TEXT, '
          '\'profileBannerUrl\' TEXT, \'profileLinkColorHexTriplet\' INTEGER, '
          '\'name\' TEXT, \'location\' TEXT, \'structuredLocation\' BLOB, '
          '\'description\' TEXT, \'url\' TEXT, \'urlEntities\' BLOB, '
          '\'bioEntities\' BLOB, \'protected\' INTEGER, \'verified\' INTEGER, '
          '\'following\' INTEGER, \'deviceFollowing\' INTEGER, '
          '\'advertiserAccountType\' INTEGER, \'statusesCount\' INTEGER, '
          '\'mediaCount\' INTEGER, \'favoritesCount\' INTEGER, '
          '\'followingCount\' INTEGER, \'followersCount\' INTEGER, '
          '\'followersCountFast\' INTEGER, \'followersCountNormal\' INTEGER, '
          '\'couldBeStale\' INTEGER, \'isLifelineInstitution\' INTEGER, '
          '\'hasCollections\' INTEGER, \'updatedAt\' REAL, \'createdDate\' '
          'REAL, \'isTranslator\' INTEGER, \'hasExtendedProfileFields\' '
          'INTEGER, \'extendedProfileFields\' BLOB, \'pinnedTweetId\' '
          'INTEGER, \'businessProfileState\' INTEGER, \'analyticsType\' '
          'INTEGER )'),
      'UsersShadow': (
          'CREATE TABLE UsersShadow ( \'id\' INTEGER PRIMARY KEY, '
          '\'screenName\' TEXT COLLATE NOCASE, \'profileImageUrl\' TEXT, '
          '\'profileBannerUrl\' TEXT, \'profileLinkColorHexTriplet\' INTEGER, '
          '\'name\' TEXT, \'location\' TEXT, \'structuredLocation\' BLOB, '
          '\'description\' TEXT, \'url\' TEXT, \'urlEntities\' BLOB, '
          '\'bioEntities\' BLOB, \'protected\' INTEGER, \'verified\' INTEGER, '
          '\'following\' INTEGER, \'deviceFollowing\' INTEGER, '
          '\'advertiserAccountType\' INTEGER, \'statusesCount\' INTEGER, '
          '\'mediaCount\' INTEGER, \'favoritesCount\' INTEGER, '
          '\'followingCount\' INTEGER, \'followersCount\' INTEGER, '
          '\'followersCountFast\' INTEGER, \'followersCountNormal\' INTEGER, '
          '\'couldBeStale\' INTEGER, \'isLifelineInstitution\' INTEGER, '
          '\'hasCollections\' INTEGER, \'updatedAt\' REAL, \'createdDate\' '
          'REAL, \'isTranslator\' INTEGER, \'hasExtendedProfileFields\' '
          'INTEGER, \'extendedProfileFields\' BLOB, \'pinnedTweetId\' '
          'INTEGER, \'businessProfileState\' INTEGER, \'analyticsType\' '
          'INTEGER )')}]

  def ParseContactRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = TwitterIOSContactEventData()
    event_data.description = self._GetRowValue(query_hash, row, 'description')
    event_data.followers_count = self._GetRowValue(
        query_hash, row, 'followersCount')
    event_data.following = self._GetRowValue(query_hash, row, 'following')
    event_data.following_count = self._GetRowValue(
        query_hash, row, 'followingCount')
    event_data.location = self._GetRowValue(query_hash, row, 'location')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.profile_url = self._GetRowValue(
        query_hash, row, 'profileImageUrl')
    event_data.query = query
    event_data.screen_name = self._GetRowValue(query_hash, row, 'screenName')
    event_data.url = self._GetRowValue(query_hash, row, 'url')

    timestamp = self._GetRowValue(query_hash, row, 'createdDate')
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'updatedAt')
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_UPDATE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseStatusRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = TwitterIOSStatusEventData()
    event_data.favorite_count = self._GetRowValue(
        query_hash, row, 'favoriteCount')
    event_data.favorited = self._GetRowValue(query_hash, row, 'favorited')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.query = query
    event_data.retweet_count = self._GetRowValue(
        query_hash, row, 'retweetCount')
    event_data.text = self._GetRowValue(query_hash, row, 'text')
    event_data.user_id = self._GetRowValue(query_hash, row, 'user_id')

    timestamp = self._GetRowValue(query_hash, row, 'date')
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'updatedAt')
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_UPDATE)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(TwitterIOSPlugin)
