# -*- coding:utf-8 -*-
"""Parser for Twitter on iOS 8+ database.

SQLite database path:
/private/var/mobile/Containers/Data/Application/Library/Caches/databases/
SQLite database name: twitter.db
"""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata
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
    screen_name (str): screen name.
    url (str): URL of the profile.
  """

  DATA_TYPE = u'twitter:ios:contact'

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
    self.screen_name = None
    self.url = None


class TwitterIOSStatusEventData(events.EventData):
  """Parent class for Twitter on iOS 8+ status events.

  Attributes:
    favorite_count (int): number of times the status message has been favorited.
    favorited (int): value to mark status as favorite by the account.
    name (str): user's profile name.
    retweet_count (str): number of times the status message has been retweeted.
    text (str): content of the status messsage.
    user_id (int): user unique identifier.
  """

  DATA_TYPE = u'twitter:ios:status'

  def __init__(self):
    """Initializes event data."""
    super(TwitterIOSStatusEventData, self).__init__(data_type=self.DATA_TYPE)
    self.favorite_count = None
    self.favorited = None
    self.name = None
    self.retweet_count = None
    self.text = None
    self.user_id = None


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
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = TwitterIOSContactEventData()
    event_data.description = row['description']
    event_data.followers_count = row['followersCount']
    event_data.following = row['following']
    event_data.following_count = row['followingCount']
    event_data.location = row['location']
    event_data.name = row['name']
    event_data.profile_url = row['profileImageUrl']
    event_data.query = query
    event_data.screen_name = row['screenName']
    event_data.url = row['url']

    timestamp = row['createdDate']
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.CREATION_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['updatedAt']
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.UPDATE_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseStatusRow(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    event_data = TwitterIOSStatusEventData()
    event_data.favorite_count = row['favoriteCount']
    event_data.favorited = row['favorited']
    event_data.name = row['name']
    event_data.query = query
    event_data.retweet_count = row['retweetCount']
    event_data.text = row['text']
    event_data.user_id = row['user_id']

    timestamp = row['date']
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.CREATION_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = row['updatedAt']
    if timestamp:
      # Convert the floating point value to an integer.
      timestamp = int(timestamp)
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.UPDATE_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(TwitterIOSPlugin)
