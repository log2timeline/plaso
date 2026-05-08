"""SQLite parser plugin for iOS Instagram threads database files.

The iOS Instagram threads database file is typically stored in:
  9368974384.db
"""

import plistlib
from plistlib import UID

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSInstagramThreadsEventData(events.EventData):
  """Instagram threads event data.

  Attributes:
    message (str): Content of the direct message or chat sent in the thread.
    query (str): SQL query that was used to obtain the event data.
    sender_identifier (str): unique identifier (or primary key) of the sender
        account.
    sent_time (dfdatetime.DateTimeValues): Date and time when the message was 
        sent.
    shared_media_identifier (str): Identifier of the media shared in the thread.
    shared_media_url (str): URL to the media content shared in the thread.
    username (str): username of the sender or participant in the thread.
    video_chat_call_identifier (str): Identifier of the video call session.
    video_chat_title (str): Title or description of the video chat.
  """

  DATA_TYPE = 'ios:instagram:thread'

  def __init__(self):
    """Initializes event data."""
    super().__init__(data_type=self.DATA_TYPE)
    self.message = None
    self.query = None
    self.sender_identifier = None
    self.shared_media_identifier = None
    self.shared_media_url = None
    self.sent_time = None
    self.username = None
    self.video_chat_call_identifier = None
    self.video_chat_title = None


class IOSInstagramPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for iOS Instagram threads database files."""

  NAME = 'instagram_ios'
  DATA_FORMAT = 'iOS Instagram threads SQLite database (9368974384.db) file'

  REQUIRED_STRUCTURE = {
      'messages': frozenset(['message_id', 'archive']),
      'threads': frozenset(['thread_id','metadata'])}

  QUERIES = [
      (('SELECT thread_id, metadata FROM threads'), 'ParseUserRow'),
      (('SELECT message_id, archive FROM messages'), 'ParseThreadRow')]

  SCHEMAS = [{
      'inbox_metadata': (
          'CREATE TABLE inbox_metadata ( sequence_id INTEGER NOT NULL, '
          'snapshot_at_ms REAL NOT NULL, snapshot_app_version TEXT NOT NULL, '
          'cursors BLOB NOT NULL, unseen_count_from_server INTEGER, '
          'business_messaging_high_volume_rate_limit_state INTEGER NOT NULL, '
          'row_id INTEGER PRIMARY KEY AUTOINCREMENT)'),
      'messages': (
          'CREATE TABLE messages ( message_id TEXT NOT NULL, '
          'thread_id TEXT NOT NULL, archive BLOB NOT NULL, '
          'class_name TEXT NOT NULL, '
          'row_id INTEGER PRIMARY KEY AUTOINCREMENT)'),
      'mutations': (
          'CREATE TABLE mutations ( mutation_id TEXT UNIQUE NOT NULL, '
          'archive BLOB NOT NULL, row_id INTEGER PRIMARY KEY AUTOINCREMENT)'),
      'quick_reply': (
          'CREATE TABLE quick_reply ( quickReplyId TEXT, shortcut TEXT, '
          'message TEXT, row_id INTEGER PRIMARY KEY AUTOINCREMENT)'),
      'sqlite_sequence': (
          'CREATE TABLE sqlite_sequence(name,seq)'),
      'thread_client_state': (
          'CREATE TABLE thread_client_state ( thread_id TEXT NOT NULL, '
          'archive BLOB NOT NULL, row_id INTEGER PRIMARY KEY AUTOINCREMENT)'),
      'threads': (
          'CREATE TABLE threads ( thread_id TEXT UNIQUE NOT NULL, '
          'thread_id_v2 TEXT, viewer_id TEXT NOT NULL, metadata BLOB, '
          'thread_messages_range BLOB, visual_message_info BLOB, '
          'row_id INTEGER PRIMARY KEY AUTOINCREMENT)')}]

  def __init__(self):
    """Initializes the plugin."""
    super().__init__()
    self.users = {}

  def ParseUserRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a thread metadata row
    
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    def GetField(obj, key, objects):
      val = obj.get(key)
      return objects[val.data] if isinstance(val, UID) else val

    metadata_blob = self._GetRowValue(query_hash, row, 'metadata')
    if not metadata_blob or not metadata_blob.startswith(b'bplist'):
      return

    try:
      plist_data = plistlib.loads(metadata_blob)
      objects = plist_data["$objects"]
      root_uid = plist_data["$top"]["root"].data
      root = objects[root_uid]

      user = GetField(root, "NSArray<IGUser *>*users", objects)
      if isinstance(user, dict) and "NS.objects" in user:
        user_uids = user["NS.objects"]
        for user_uid in user_uids:
          user_obj = (
            objects[user_uid.data]
            if isinstance(user_uid, UID)
            else user_uid
        )
          if isinstance(user_obj, dict):
            user_pk = GetField(user_obj, "pk", objects)
            user_full_name = GetField(user_obj, "fullName", objects)
            if user_full_name:
              self.users[user_pk] = user_full_name
            else:
              self.users[user_pk] = None

      inviter = GetField(root, "IGUser*inviter", objects)
      if inviter:
        inviter_pk = GetField(inviter, "pk", objects)
        inviter_full_name = GetField(inviter, "fullName", objects)
        if inviter_full_name:
          self.users[inviter_pk] = inviter_full_name
        else:
          self.users[inviter_pk] = None

    except (AttributeError, IndexError, KeyError, TypeError,
            plistlib.InvalidFileException) as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Unable to parse thread metadata with error: {exception!s}')

  def ParseThreadRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a message row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    def GetField(obj, key, objects):
      val = obj.get(key)
      return objects[val.data] if isinstance(val, UID) else val

    def GetNestedField(obj, keys, objects):
      try:
        for key in keys:
          obj = GetField(obj, key, objects)
        return obj
      except (AttributeError, KeyError, IndexError, TypeError):
        return None

    message_identifier = self._GetRowValue(query_hash, row, 'message_id')
    archive_blob = self._GetRowValue(query_hash, row, 'archive')

    if not archive_blob or not archive_blob.startswith(b'bplist'):
      return

    try:
      plist_data = plistlib.loads(archive_blob)
      objects = plist_data["$objects"]
      root_uid = plist_data["$top"]["root"].data
      root = objects[root_uid]

      metadata = GetField(
            root, "IGDirectPublishedMessageMetadata*metadata", objects)
      if metadata:
        sender_identifier = GetField(metadata, "NSString*senderPk", objects)
        server_timestamp_raw = GetField(
                metadata, "NSDate*serverTimestamp", objects)
      else:
        sender_identifier = None
        server_timestamp_raw = None

      server_timestamp = None
      if isinstance(
        server_timestamp_raw, dict) and "NS.time" in server_timestamp_raw:
        timestamp_value = server_timestamp_raw["NS.time"]
        server_timestamp = dfdatetime_cocoa_time.CocoaTime(
                timestamp=timestamp_value)

      content = GetField(
            root, "IGDirectPublishedMessageContent*content", objects)
      if content:
        message = GetField(content, "NSString*string", objects)
        thread_activity = GetField(
            content,
            "IGDirectThreadActivityAnnouncement*threadActivity", 
            objects
        )
        media = GetField(
                content, "IGDirectPublishedMessageMedia*media", objects)
      else:
        message = None
        thread_activity = None
        media = None

      if thread_activity:
        video_chat_title = GetField(
            thread_activity, "NSString*voipTitle", objects)
        video_chat_call_identifier = GetField(
            thread_activity, "NSString*videoCallId", objects)
      else:
        video_chat_title = None
        video_chat_call_identifier = None

      shared_media_identifier = None
      shared_media_url = None
      if media:
        shared_media_identifier = GetNestedField(media, [
          "IGDirectPublishedMessagePermanentMedia*permanentMedia",
          "IGPhoto*photo",
          "kIGPhotoMediaID"
            ], objects)
        image_versions = GetNestedField(media, [
          "IGDirectPublishedMessagePermanentMedia*permanentMedia",
          "IGPhoto*photo",
          "imageVersions"
            ], objects)
        if isinstance(
          image_versions, dict) and "NS.objects" in image_versions:
          first_image_uid = image_versions["NS.objects"][0]
          if isinstance(first_image_uid, UID):
            first_image_obj = objects[first_image_uid.data]
            shared_media_url = GetNestedField(first_image_obj, [
              "url",
              "NS.relative"
            ], objects)

      username = None
      if sender_identifier:
        username = self.users.get(sender_identifier)

      event_data = IOSInstagramThreadsEventData()
      event_data.message = message
      event_data.query = query
      event_data.sender_identifier = sender_identifier
      event_data.sent_time = server_timestamp
      event_data.shared_media_identifier = shared_media_identifier
      event_data.shared_media_url = shared_media_url
      event_data.username = username
      event_data.video_chat_call_identifier = video_chat_call_identifier
      event_data.video_chat_title = video_chat_title

      parser_mediator.ProduceEventData(event_data)

    except (AttributeError, IndexError, KeyError, TypeError,
            plistlib.InvalidFileException) as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Unable to parse archive for message_id {message_identifier:s} '
          f'with error: {exception!s}')


sqlite.SQLiteParser.RegisterPlugin(IOSInstagramPlugin)
