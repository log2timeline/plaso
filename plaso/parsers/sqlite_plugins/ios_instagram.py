"""SQLite parser plugin for iOS Instagram threads database files.

The iOS Instagram threads database file is typically stored in:
  9368974384.db
"""

import plistlib

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.parsers.sqlite_plugins import interface


class IOSInstagramMessageEventData(events.EventData):
  """Instagram message event data.

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

  DATA_TYPE = 'ios:instagram:message'

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

  # Note that the threads table is processed first to determine the usernames.
  QUERIES = [
      (('SELECT thread_id, metadata FROM threads'), '_ParseThreadsRow'),
      (('SELECT message_id, archive FROM messages'), '_ParseMessagesRow')]

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
    self._plist_decoder = plist_interface.NSKeyedArchiverDecoder()

  def _ParseMessagesRow(
      self, parser_mediator, query, row, cache=None, **unused_kwargs):
    """Parses a row in the messages table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
    """
    query_hash = hash(query)

    message_identifier = self._GetRowValue(query_hash, row, 'message_id')

    archive = self._GetRowValue(query_hash, row, 'archive')
    if not archive:
      parser_mediator.ProduceExtractionWarning(
          f'Message: {message_identifier:s} missing archive value')
      return

    if not archive.startswith(b'bplist'):
      parser_mediator.ProduceExtractionWarning(
          f'Message: {message_identifier:s} unsupported archive value - not a '
          f'binary plist.')
      return

    try:
      top_level_object = plistlib.loads(archive)

    except plistlib.InvalidFileException as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Message: {message_identifier:s} unable to parse archive plist with '
          f'error: {exception!s}')
      return

    if not self._plist_decoder.IsEncoded(top_level_object):
      parser_mediator.ProduceExtractionWarning(
          f'Message: {message_identifier:s} unsupported archive plist '
          f'encoding.')
      return

    decoded_plist = self._plist_decoder.Decode(top_level_object)

    content = decoded_plist.get('IGDirectPublishedMessageContent*content', {})
    metadata = decoded_plist.get(
        'IGDirectPublishedMessageMetadata*metadata', {})

    media = content.get('IGDirectPublishedMessageMedia*media', {})
    thread_activity = content.get(
        'IGDirectThreadActivityAnnouncement*threadActivity', {})

    photo = media.get(
        'IGDirectPublishedMessagePermanentMedia*permanentMedia', {}).get(
            'IGPhoto*photo', {})
    image_versions = photo.get('imageVersions')

    event_data = IOSInstagramMessageEventData()
    event_data.message = content.get('NSString*string')
    event_data.query = query
    event_data.sender_identifier = metadata.get('NSString*senderPk')
    event_data.sent_time = metadata.get('NSDate*serverTimestamp')
    event_data.shared_media_identifier = photo.get('kIGPhotoMediaID')
    event_data.video_chat_call_identifier = thread_activity.get(
        'NSString*videoCallId')
    event_data.video_chat_title = thread_activity.get('NSString*voipTitle')

    if event_data.sender_identifier:
      usernames = cache.GetResults('usernames', default_value={})
      event_data.username = usernames.get(event_data.sender_identifier)
    if image_versions:
      event_data.shared_media_url = image_versions[0].get("url")

    parser_mediator.ProduceEventData(event_data)

  def _ParseThreadsRow(
      self, parser_mediator, query, row, cache=None, **unused_kwargs):
    """Parses a row in the threads table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
      cache (Optional[SQLiteCache]): cache.
    """
    query_hash = hash(query)

    thread_identifier = self._GetRowValue(query_hash, row, 'thread_id')

    metadata = self._GetRowValue(query_hash, row, 'metadata')
    if not metadata:
      return

    if not metadata.startswith(b'bplist'):
      parser_mediator.ProduceExtractionWarning(
          f'Thread: {thread_identifier:s} unsupported metadata - not a binary '
          f'plist.')
      return

    try:
      top_level_object = plistlib.loads(metadata)

    except plistlib.InvalidFileException as exception:
      parser_mediator.ProduceExtractionWarning(
          f'Thread: {thread_identifier:s} unable to parse metadata plist with '
          f'error: {exception!s}')
      return

    if not self._plist_decoder.IsEncoded(top_level_object):
      parser_mediator.ProduceExtractionWarning(
          f'Thread: {thread_identifier:s} unsupported metadata plist encoding.')
      return

    decoded_plist = self._plist_decoder.Decode(top_level_object)

    usernames = cache.GetResults('usernames', default_value={})

    inviter = decoded_plist.get('IGUser*inviter', {})
    user_identifier = inviter.get("pk")
    if user_identifier:
      usernames[user_identifier] = inviter.get("fullName") or None

    for user in decoded_plist.get('NSArray<IGUser *>*users') or []:
      user_identifier = user.get("pk")
      if user_identifier:
        usernames[user_identifier] = user.get("fullName") or None

    cache.SetResults('usernames', usernames)


sqlite.SQLiteParser.RegisterPlugin(IOSInstagramPlugin)
