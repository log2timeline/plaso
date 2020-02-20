# -*- coding:utf-8 -*-
"""Parser for Tango on Android databases."""

from __future__ import unicode_literals

import codecs
from base64 import b64decode as base64_decode

from dfdatetime import java_time as dfdatetime_java_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class TangoAndroidMessageEventData(events.EventData):
  """Tango on Android message event data.

  Attributes:
    message_identifier (int): message identifier.
    direction (int): flag indicating direction of the message.
  """

  DATA_TYPE = 'tango:android:message'

  def __init__(self):
    """Initializes event data."""
    super(TangoAndroidMessageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.message_identifier = None
    self.direction = None


class TangoAndroidConversationEventData(events.EventData):
  """Tango on Android conversation event data.

  Attributes:
    conversation_identifier (int): conversation identifier.
  """

  DATA_TYPE = 'tango:android:conversation'

  def __init__(self):
    """Initializes event data."""
    super(TangoAndroidConversationEventData,
          self).__init__(data_type=self.DATA_TYPE)
    self.conversation_identifier = None


class TangoAndroidContactEventData(events.EventData):
  """Tango on Android contact event data.

  Attributes:
    first_name (str): contact profile first name.
    last_name (str): contact profile last name.
    birthday (str): contact profile birthday.
    gender (str): contact profile gender.
    status (str): contact status message.
    distance (int): contact profile distance.
    is_friend (bool): True if the contact is considered a friend.
    friend_request_type (str): flag indicating the type of friend request sent
        for example outRequest for request sent or noRequest for no request.
    friend_request_message (str): message sent on friend request.
  """

  DATA_TYPE = 'tango:android:contact'

  def __init__(self):
    """Initializes event data."""
    super(TangoAndroidContactEventData, self).__init__(data_type=self.DATA_TYPE)
    self.first_name = None
    self.last_name = None
    self.birthday = None
    self.gender = None
    self.status = None
    self.distance = None
    self.is_friend = None
    self.friend_request_type = None
    self.friend_request_message = None


class TangoAndroidTCPlugin(interface.SQLitePlugin):
  """Parser for Tango on Android tc database."""

  NAME = 'tango_android_tc'
  DESCRIPTION = 'Parser for Tango on Android tc database.'

  REQUIRED_STRUCTURE = {
      'conversations': frozenset([
          'conv_id', 'payload']),
      'messages': frozenset([
          'create_time', 'send_time', 'msg_id', 'payload', 'direction']),
      'likes': frozenset([
          'msg_id'])}

  QUERIES = [
      (('SELECT conversations.conv_id AS conv_id, conversations.payload AS '
        'payload FROM conversations'), 'ParseConversationRow'),
      (('SELECT messages.create_time AS create_time, messages.send_time AS '
        'send_time, messages.msg_id AS msg_id, messages.payload AS payload, '
        'messages.direction AS direction FROM messages LEFT JOIN likes ON '
        'messages.msg_id = likes.msg_id'), 'ParseMessageRow')]

  SCHEMAS = [{
      'conversations': (
          'CREATE TABLE `conversations` (`conv_id` TEXT PRIMARY KEY, '
          '`conv_type` INTEGER DEFAULT 0, `payload` BLOB, `last_msg_id` '
          'INTEGER, `unread_count` INTEGER, `last_read_sent_msg_id` INTEGER, '
          '`conv_del_status` INTEGER DEFAULT 0, `deleting_ts` BIGINT DEFAULT '
          '0, `conv_restore_status` INTEGER DEFAULT 0, `peers_read` TEXT, '
          '`total_received_msg_count` INTEGER DEFAULT -1, '
          '`communication_context` INTEGER DEFAULT 0)'),
      'games': (
          'CREATE TABLE `games` (`game_session_id` TEXT PRIMARY KEY, '
          '`message_id` INTEGER, `conversation_id` TEXT, `game_id` TEXT, '
          '`game_state` INTEGER, `action_timestamp` BIGINT, '
          '`current_player_account_id` TEXT)'),
      'likes': (
          'CREATE TABLE `likes` (`msg_id` INTEGER PRIMARY KEY, '
          '`global_msg_id` TEXT, `conv_id` TEXT, `liker_aid` TEXT, `act_type` '
          'INTEGER, `status` INTEGER, `act_ts` BIGINT, `payload` BLOB)'),
      'messages': (
          'CREATE TABLE `messages` (`msg_id` INTEGER PRIMARY KEY, `conv_id` '
          'TEXT, `type` INTEGER, `media_id` TEXT, `share_id` TEXT, '
          '`create_time` BIGINT, `send_time` BIGINT, `direction` INTEGER, '
          '`status` INTEGER, `payload` BLOB, `del_status` INTEGER)'),
      'profiles': (
          'CREATE TABLE `profiles` (`key` TEXT PRIMARY KEY, `value` TEXT)'),
      'receipts': (
          'CREATE TABLE `receipts` (`conv_id` TEXT PRIMARY KEY, `msg_id` '
          'INTEGER, `sender_msg_id` INTEGER, `sender_aids` TEXT, `type` '
          'INTEGER, `create_time` BIGINT, `status` INTEGER, `payload` BLOB)'),
      'sms': (
          'CREATE TABLE `sms` (`msg_id` INTEGER PRIMARY KEY, `phonenumber` '
          'TEXT, `text` TEXT)')}]

  def ParseConversationRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a conversation row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = TangoAndroidConversationEventData()
    event_data.conversation_identifier = self._GetRowValue(
        query_hash, row, 'conv_id')

    # TODO: payload is a base64 encoded binary blob, we need to find the
    # structure to extract the relevant bits.
    # event_data.payload = self._GetRowValue(query_hash, row, 'payload')

    date_time = dfdatetime_semantic_time.NotSet()
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseMessageRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = TangoAndroidMessageEventData()
    event_data.message_identifier = self._GetRowValue(
        query_hash, row, 'msg_id')

    # TODO: payload is a base64 encoded binary blob, we need to find the
    # structure to extract the relevant bits.
    # event_data.payload = self._GetRowValue(query_hash, row, 'payload')

    event_data.direction = self._GetRowValue(query_hash, row, 'direction')

    timestamp = self._GetRowValue(query_hash, row, 'create_time')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'send_time')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_SENT)
      parser_mediator.ProduceEventWithEventData(event, event_data)


class TangoAndroidProfilePlugin(interface.SQLitePlugin):
  """Parser for Tango on Android profile database."""

  NAME = 'tango_android_profile'
  DESCRIPTION = 'Parser for Tango on Android profile database.'

  REQUIRED_STRUCTURE = {
      'profiletable': frozenset([
          'itemLastActiveTime', 'itemLastLocalAccessTime',
          'itemFriendRequestTime', 'itemFirstName', 'itemLastName',
          'itemBirthday', 'itemGender', 'itemStatus', 'itemDistance',
          'itemIsFriend', 'itemFriendRequestType', 'itemFriendRequestMessage'])}

  QUERIES = [
      (('SELECT itemLastActiveTime AS last_active_time, itemLastLocalAccessTime'
        ' AS last_access_time, itemFriendRequestTime AS friend_request_time, '
        'itemFirstName AS first_name, itemLastName AS last_name, itemBirthday '
        'AS birthday, itemGender AS gender, itemStatus AS status, itemDistance '
        'AS distance, itemIsFriend AS friend, itemFriendRequestType AS '
        'friend_request_type, itemFriendRequestMessage AS '
        'friend_request_message FROM profiletable'), 'ParseContactRow')]

  SCHEMAS = [{
      'profiles': (
          'CREATE TABLE `profiles` (`key` TEXT PRIMARY KEY, `value` TEXT)'),
      'profiletable': (
          'CREATE TABLE `profiletable` (`itemUserId` TEXT PRIMARY KEY, '
          '`itemFirstName` TEXT NOT NULL, `itemLastName` TEXT NOT NULL, '
          '`itemBirthday` TEXT NOT NULL, `itemGender` TEXT NOT NULL, '
          '`itemStatus` TEXT NOT NULL, `itemLastActiveTime` BIGINT NOT NULL, '
          '`itemDistance` DOUBLE NOT NULL, `itemCity` TEXT NOT NULL, '
          '`itemGeoCountryCode` TEXT NOT NULL, `itemAvatarUrl` TEXT NOT NULL, '
          '`itemThumbnailUrl` TEXT NOT NULL, `itemVideoUrl` TEXT NOT NULL, '
          '`itemVideoThumbnailUrl` TEXT NOT NULL, `itemBackgroundUrl` TEXT '
          'NOT NULL, `itemIsFriend` INTEGER NOT NULL, `itemIsBlocked` INTEGER '
          'NOT NULL, `itemFriendRequestType` TEXT NOT NULL, '
          '`itemReverseRelationships` TEXT NOT NULL, `itemFavoriterCount` '
          'INTEGER NOT NULL, `itemFavoritingCount` INTEGER NOT NULL, '
          '`itemFeedCount` INTEGER NOT NULL, `itemRefereneCount` INTEGER NOT '
          'NULL, `itemLevel1DataSyncTime` BIGINT NOT NULL, '
          '`itemLevel2DataSyncTime` BIGINT NOT NULL, `itemLevel3DataSyncTime` '
          'BIGINT NOT NULL, `itemLevel4DataSyncTime` BIGINT NOT NULL, '
          '`itemLevel5DataSyncTime` BIGINT NOT NULL, '
          '`itemLastLocalAccessTime` BIGINT NOT NULL, `itemFriendRequestId` '
          'TEXT NOT NULL, `itemFriendRequestMessage` TEXT NOT NULL, '
          '`itemFriendRequestTime` BIGINT NOT NULL, `itemIsNewFriendRequest` '
          'INTEGER NOT NULL, `itemFriendRequestTCMessageId` INTEGER NOT NULL, '
          '`itemFriendRequestContext` TEXT NOT NULL, '
          '`itemFriendRequestAttachedPostType` INTEGER NOT NULL, '
          '`itemFriendRequestAttachedPostContent` TEXT NOT NULL, '
          '`itemFriendRequestHasBeenForwardedToTc` INTEGER NOT NULL, '
          '`itemProfileType` TEXT NOT NULL, `itemDatingAge` INTEGER NOT NULL, '
          '`itemDatingLocationString` TEXT NOT NULL, '
          '`itemDatingSeekingString` TEXT NOT NULL, `itemDatingEssayText` '
          'TEXT NOT NULL, `itemDatingBodyType` TEXT NOT NULL, '
          '`itemDatingLastActive` TEXT NOT NULL, `itemDatingProfileUrl` TEXT '
          'NOT NULL, `itemLastTimeOfLikeProfile` BIGINT NOT NULL, '
          '`itemIsHidden` INTEGER NOT NULL, `itemPrivacy` INTEGER NOT NULL, '
          '`itemCanSeeMyPost` INTEGER NOT NULL, `itemCanShareMyPost` INTEGER '
          'NOT NULL, `itemCanContactMe` INTEGER NOT NULL)')}]

  def ParseContactRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a contact row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = TangoAndroidContactEventData()

    first_name = self._GetRowValue(query_hash, row, 'first_name')
    try:
      decoded_text = base64_decode(first_name)
      event_data.first_name = codecs.decode(decoded_text, 'utf-8')
    except ValueError:
      event_data.first_name = first_name
      parser_mediator.ProduceExtractionWarning(
          'unable to parse first name: {0:s}'.format(first_name))

    last_name = self._GetRowValue(query_hash, row, 'last_name')
    try:
      decoded_text = base64_decode(last_name)
      event_data.last_name = codecs.decode(decoded_text, 'utf-8')
    except ValueError:
      event_data.last_name = last_name
      parser_mediator.ProduceExtractionWarning(
          'unable to parse last name: {0:s}'.format(last_name))

    event_data.birthday = self._GetRowValue(query_hash, row, 'birthday')
    event_data.gender = self._GetRowValue(query_hash, row, 'gender')

    status = self._GetRowValue(query_hash, row, 'status')
    try:
      decoded_text = base64_decode(status)
      event_data.status = codecs.decode(decoded_text, 'utf-8')
    except ValueError:
      event_data.status = status
      parser_mediator.ProduceExtractionWarning(
          'unable to parse status: {0:s}'.format(status))

    event_data.distance = self._GetRowValue(query_hash, row, 'distance')

    is_friend = self._GetRowValue(query_hash, row, 'friend')
    event_data.is_friend = False
    if is_friend:
      event_data.is_friend = True

    event_data.friend_request_type = self._GetRowValue(
        query_hash, row, 'friend_request_type')

    friend_request_message = self._GetRowValue(
        query_hash, row, 'friend_request_message')
    try:
      decoded_text = base64_decode(friend_request_message)
      event_data.friend_request_message = codecs.decode(decoded_text, 'utf-8')
    except ValueError:
      event_data.friend_request_message = friend_request_message
      parser_mediator.ProduceExtractionWarning(
          'unable to parse status: {0:s}'.format(friend_request_message))

    timestamp = self._GetRowValue(query_hash, row, 'last_active_time')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACTIVE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'last_access_time')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'friend_request_time')
    if timestamp:
      date_time = dfdatetime_java_time.JavaTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_SENT)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugins([
    TangoAndroidTCPlugin, TangoAndroidProfilePlugin])
