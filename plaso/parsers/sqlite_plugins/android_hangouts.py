# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google Hangouts conversations database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidHangoutsMessageData(events.EventData):
  """Google Hangouts Message event data.

  Attributes:
    body (str): content of the SMS text message.
    creation_time (dfdatetime.DateTimeValues): date and time the Google Hangouts
        message was created.
    message_status (int): message status.
    message_type (int): message type.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    sender (str): Name with the sender.
  """

  DATA_TYPE = 'android:messaging:hangouts'

  def __init__(self):
    """Initializes event data."""
    super(AndroidHangoutsMessageData, self).__init__(data_type=self.DATA_TYPE)
    self.body = None
    self.creation_time = None
    self.message_status = None
    self.message_type = None
    self.offset = None
    self.query = None
    self.sender = None


class AndroidHangoutsMessagePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Google Hangouts conversations database files.

  The Google Hangouts conversations database file is typically stored in:
  /data/com.google.android.talk/databases/babel.db

  This SQLite database is the conversation database for conversations,
  participant names, messages, and information about the Google Hangout event.
  There can be multiple babel.db databases, and each database name will be
  followed by an integer starting with 0, for example:
  "babel0.db,babel1.db,babel3.db".
  """

  NAME = 'hangouts_messages'
  DATA_FORMAT = 'Google Hangouts conversations SQLite database (babel.db) file'

  REQUIRED_STRUCTURE = {
      'blocked_people': frozenset([]),
      'messages': frozenset([
          '_id', 'text', 'timestamp', 'status', 'type', 'author_chat_id']),
      'participants': frozenset([
          'full_name', 'chat_id'])}

  QUERIES = [
      ('SELECT messages._id, participants.full_name, text, messages.timestamp,'
       'status, type FROM messages INNER JOIN participants ON '
       'messages.author_chat_id=participants.chat_id;', 'ParseMessagesRow')]

  SCHEMAS = [{
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'blocked_people': (
          'CREATE TABLE blocked_people (_id INTEGER PRIMARY KEY, gaia_id '
          'TEXT, chat_id TEXT, name TEXT, profile_photo_url TEXT, UNIQUE '
          '(chat_id) ON CONFLICT REPLACE, UNIQUE (gaia_id) ON CONFLICT '
          'REPLACE)'),
      'conversation_participants': (
          'CREATE TABLE conversation_participants (_id INTEGER PRIMARY KEY, '
          'participant_row_id INT, participant_type INT, conversation_id '
          'TEXT, sequence INT, active INT, invitation_status INT DEFAULT(0), '
          'UNIQUE (conversation_id,participant_row_id) ON CONFLICT REPLACE, '
          'FOREIGN KEY (conversation_id) REFERENCES '
          'conversations(conversation_id) ON DELETE CASCADE ON UPDATE '
          'CASCADE, FOREIGN KEY (participant_row_id) REFERENCES '
          'participants(_id))'),
      'conversations': (
          'CREATE TABLE conversations (_id INTEGER PRIMARY KEY, '
          'conversation_id TEXT, conversation_type INT, '
          'latest_message_timestamp INT DEFAULT(0), '
          'latest_message_expiration_timestamp INT, metadata_present '
          'INT,notification_level INT, name TEXT, generated_name TEXT, '
          'snippet_type INT, snippet_text TEXT, snippet_image_url TEXT, '
          'snippet_author_gaia_id TEXT, snippet_author_chat_id TEXT, '
          'snippet_message_row_id INT, snippet_selector INT, snippet_status '
          'INT, snippet_new_conversation_name TEXT, snippet_participant_keys '
          'TEXT, snippet_sms_type TEXT, previous_latest_timestamp INT, status '
          'INT, view INT, inviter_gaia_id TEXT, inviter_chat_id TEXT, '
          'inviter_affinity INT, is_pending_leave INT, account_id INT, is_otr '
          'INT, packed_avatar_urls TEXT, self_avatar_url TEXT, self_watermark '
          'INT DEFAULT(0), chat_watermark INT DEFAULT(0), hangout_watermark '
          'INT DEFAULT(0), is_draft INT, sequence_number INT, call_media_type '
          'INT DEFAULT(0), has_joined_hangout INT, has_chat_notifications '
          'DEFAULT(0),has_video_notifications '
          'DEFAULT(0),last_hangout_event_time INT, draft TEXT, otr_status '
          'INT, otr_toggle INT, last_otr_modification_time INT, '
          'continuation_token BLOB, continuation_event_timestamp INT, '
          'has_oldest_message INT DEFAULT(0), sort_timestamp INT, '
          'first_peak_scroll_time INT, first_peak_scroll_to_message_timestamp '
          'INT, second_peak_scroll_time INT, '
          'second_peak_scroll_to_message_timestamp INT, conversation_hash '
          'BLOB, disposition INT DEFAULT(0), has_persistent_events INT '
          'DEFAULT(-1), transport_type INT DEFAULT(1), '
          'default_transport_phone TEXT, sms_service_center TEXT, '
          'is_temporary INT DEFAULT (0), sms_thread_id INT DEFAULT (-1), '
          'chat_ringtone_uri TEXT, hangout_ringtone_uri TEXT, '
          'snippet_voicemail_duration INT DEFAULT (0), share_count INT '
          'DEFAULT(0), has_unobserved TEXT, last_share_timestamp INT '
          'DEFAULT(0), gls_status INT DEFAULT(0), gls_link TEXT, is_guest INT '
          'DEFAULT(0), UNIQUE (conversation_id ))'),
      'dismissed_contacts': (
          'CREATE TABLE dismissed_contacts (_id INTEGER PRIMARY KEY, gaia_id '
          'TEXT, chat_id TEXT, name TEXT, profile_photo_url TEXT, UNIQUE '
          '(chat_id) ON CONFLICT REPLACE, UNIQUE (gaia_id) ON CONFLICT '
          'REPLACE)'),
      'event_suggestions': (
          'CREATE TABLE event_suggestions (_id INTEGER PRIMARY KEY, '
          'conversation_id TEXT, event_id TEXT, suggestion_id TEXT, timestamp '
          'INT, expiration_time_usec INT, type INT, gem_asset_url STRING, '
          'gem_horizontal_alignment INT, matched_message_substring TEXT, '
          'FOREIGN KEY (conversation_id) REFERENCES '
          'conversations(conversation_id) ON DELETE CASCADE ON UPDATE '
          'CASCADE, UNIQUE (conversation_id,suggestion_id) ON CONFLICT '
          'REPLACE)'),
      'merge_keys': (
          'CREATE TABLE merge_keys (_id INTEGER PRIMARY KEY, conversation_id '
          'TEXT, merge_key TEXT, UNIQUE (conversation_id) ON CONFLICT '
          'REPLACE, FOREIGN KEY (conversation_id) REFERENCES '
          'conversations(conversation_id) ON DELETE CASCADE ON UPDATE CASCADE '
          ')'),
      'merged_contact_details': (
          'CREATE TABLE merged_contact_details (_id INTEGER PRIMARY KEY, '
          'merged_contact_id INT, lookup_data_type INT, lookup_data TEXT, '
          'lookup_data_standardized TEXT, lookup_data_search TEXT, '
          'lookup_data_label TEXT, needs_gaia_ids_resolved INT DEFAULT (1), '
          'is_hangouts_user INT DEFAULT (0), gaia_id TEXT, avatar_url TEXT, '
          'display_name TEXT, last_checked_ts INT DEFAULT (0), '
          'lookup_data_display TEXT, detail_affinity_score REAL DEFAULT '
          '(0.0), detail_logging_id TEXT, is_in_viewer_dasher_domain INT '
          'DEFAULT (0), FOREIGN KEY (merged_contact_id) REFERENCES '
          'merged_contacts(_id) ON DELETE CASCADE ON UPDATE CASCADE)'),
      'merged_contacts': (
          'CREATE TABLE merged_contacts (_id INTEGER PRIMARY KEY, '
          'contact_lookup_key TEXT, contact_id INT, raw_contact_id INT, '
          'display_name TEXT, avatar_url TEXT, is_frequent INT DEFAULT (0), '
          'is_favorite INT DEFAULT (0), contact_source INT DEFAULT(0), '
          'frequent_order INT, person_logging_id TEXT, person_affinity_score '
          'REAL DEFAULT (0.0), is_in_same_domain INT DEFAULT (0))'),
      'messages': (
          'CREATE TABLE messages (_id INTEGER PRIMARY KEY, message_id TEXT, '
          'message_type INT, conversation_id TEXT, author_chat_id TEXT, '
          'author_gaia_id TEXT, text TEXT, timestamp INT, '
          'delete_after_read_timetamp INT, status INT, type INT, local_url '
          'TEXT, remote_url TEXT, attachment_content_type TEXT, width_pixels '
          'INT, height_pixels INT, stream_id TEXT, image_id TEXT, album_id '
          'TEXT, latitude DOUBLE, longitude DOUBLE, address ADDRESS, '
          'notification_level INT, expiration_timestamp INT, '
          'notified_for_failure INT DEFAULT(0), off_the_record INT '
          'DEFAULT(0), transport_type INT NOT NULL DEFAULT(1), '
          'transport_phone TEXT, external_ids TEXT, sms_timestamp_sent INT '
          'DEFAULT(0), sms_priority INT DEFAULT(0), sms_message_size INT '
          'DEFAULT(0), mms_subject TEXT, sms_raw_sender TEXT, '
          'sms_raw_recipients TEXT, persisted INT DEFAULT(1), '
          'sms_message_status INT DEFAULT(-1), sms_type INT DEFAULT(-1), '
          'stream_url TEXT, attachment_target_url TEXT, attachment_name TEXT, '
          'image_rotation INT DEFAULT (0), new_conversation_name TEXT, '
          'participant_keys TEXT, forwarded_mms_url TEXT, forwarded_mms_count '
          'INT DEFAULT(0), attachment_description TEXT, '
          'attachment_target_url_description TEXT, attachment_target_url_name '
          'TEXT, attachment_blob_data BLOB,attachment_uploading_progress INT '
          'DEFAULT(0), sending_error INT DEFAULT(0), stream_expiration INT, '
          'voicemail_length INT DEFAULT (0), call_media_type INT DEFAULT(0), '
          'last_seen_timestamp INT DEFAULT(0), observed_status INT '
          'DEFAULT(2), receive_type INT DEFAULT(0), init_timestamp INT '
          'DEFAULT(0), in_app_msg_latency INT DEFAULT(0), notified INT '
          'DEFAULT(0), alert_in_conversation_list INT DEFAULT(0), attachments '
          'BLOB, is_user_mentioned INT DEFAULT(0), local_id TEXT, '
          'request_task_row_id INT DEFAULT(-1), FOREIGN KEY (conversation_id) '
          'REFERENCES conversations(conversation_id) ON DELETE CASCADE ON '
          'UPDATE CASCADE, UNIQUE (conversation_id,message_id) ON CONFLICT '
          'REPLACE)'),
      'mms_notification_inds': (
          'CREATE TABLE mms_notification_inds (_id INTEGER PRIMARY KEY, '
          'content_location TEXT, transaction_id TEXT, from_address TEXT, '
          'message_size INT DEFAULT(0), expiry INT)'),
      'multipart_attachments': (
          'CREATE TABLE multipart_attachments (_id INTEGER PRIMARY KEY, '
          'message_id TEXT, conversation_id TEXT, url TEXT, content_type '
          'TEXT, width INT, height INT, FOREIGN KEY (message_id, '
          'conversation_id) REFERENCES messages(message_id, conversation_id) '
          'ON DELETE CASCADE ON UPDATE CASCADE)'),
      'participant_email_fts': (
          'CREATE VIRTUAL TABLE participant_email_fts USING '
          'fts4(content="merged_contact_details", gaia_id,lookup_data)'),
      'participant_email_fts_docsize': (
          'CREATE TABLE \'participant_email_fts_docsize\'(docid INTEGER '
          'PRIMARY KEY, size BLOB)'),
      'participant_email_fts_segdir': (
          'CREATE TABLE \'participant_email_fts_segdir\'(level INTEGER,idx '
          'INTEGER,start_block INTEGER,leaves_end_block INTEGER,end_block '
          'INTEGER,root BLOB,PRIMARY KEY(level, idx))'),
      'participant_email_fts_segments': (
          'CREATE TABLE \'participant_email_fts_segments\'(blockid INTEGER '
          'PRIMARY KEY, block BLOB)'),
      'participant_email_fts_stat': (
          'CREATE TABLE \'participant_email_fts_stat\'(id INTEGER PRIMARY '
          'KEY, value BLOB)'),
      'participants': (
          'CREATE TABLE participants (_id INTEGER PRIMARY KEY, '
          'participant_type INT DEFAULT 1, gaia_id TEXT, chat_id TEXT, '
          'phone_id TEXT, circle_id TEXT, first_name TEXT, full_name TEXT, '
          'fallback_name TEXT, profile_photo_url TEXT, batch_gebi_tag STRING '
          'DEFAULT(\'-1\'), blocked INT DEFAULT(0), in_users_domain BOOLEAN, '
          'UNIQUE (circle_id) ON CONFLICT REPLACE, UNIQUE (chat_id) ON '
          'CONFLICT REPLACE, UNIQUE (gaia_id) ON CONFLICT REPLACE)'),
      'participants_fts': (
          'CREATE VIRTUAL TABLE participants_fts USING '
          'fts4(content="participants",gaia_id,full_name)'),
      'participants_fts_docsize': (
          'CREATE TABLE \'participants_fts_docsize\'(docid INTEGER PRIMARY '
          'KEY, size BLOB)'),
      'participants_fts_segdir': (
          'CREATE TABLE \'participants_fts_segdir\'(level INTEGER,idx '
          'INTEGER,start_block INTEGER,leaves_end_block INTEGER,end_block '
          'INTEGER,root BLOB,PRIMARY KEY(level, idx))'),
      'participants_fts_segments': (
          'CREATE TABLE \'participants_fts_segments\'(blockid INTEGER PRIMARY '
          'KEY, block BLOB)'),
      'participants_fts_stat': (
          'CREATE TABLE \'participants_fts_stat\'(id INTEGER PRIMARY KEY, '
          'value BLOB)'),
      'presence': (
          'CREATE TABLE presence (_id INTEGER PRIMARY KEY, gaia_id TEXT NOT '
          'NULL, reachable INT DEFAULT(0), reachable_time INT DEFAULT(0), '
          'available INT DEFAULT(0), available_time INT DEFAULT(0), '
          'status_message TEXT, status_message_time INT DEFAULT(0), call_type '
          'INT DEFAULT(0), call_type_time INT DEFAULT(0), device_status INT '
          'DEFAULT(0), device_status_time INT DEFAULT(0), last_seen INT '
          'DEFAULT(0), last_seen_time INT DEFAULT(0), location BLOB, '
          'location_time INT DEFAULT(0), UNIQUE (gaia_id) ON CONFLICT '
          'REPLACE)'),
      'recent_calls': (
          'CREATE TABLE recent_calls (_id INTEGER PRIMARY KEY, '
          'normalized_number TEXT NOT NULL, phone_number TEXT, contact_id '
          'TEXT, call_timestamp INT, call_type INT, contact_type INT, '
          'call_rate TEXT, is_free_call BOOLEAN)'),
      'search': (
          'CREATE TABLE search (search_key TEXT NOT NULL,continuation_token '
          'TEXT,PRIMARY KEY (search_key))'),
      'sticker_albums': (
          'CREATE TABLE sticker_albums (album_id TEXT NOT NULL, title TEXT, '
          'cover_photo_id TEXT, last_used INT DEFAULT(0), PRIMARY KEY '
          '(album_id))'),
      'sticker_photos': (
          'CREATE TABLE sticker_photos (photo_id TEXT NOT NULL, album_id TEXT '
          'NOT NULL, url TEXT NOT NULL, file_name TEXT, last_used INT '
          'DEFAULT(0), PRIMARY KEY (photo_id), FOREIGN KEY (album_id) '
          'REFERENCES sticker_albums(album_id) ON DELETE CASCADE)'),
      'suggested_contacts': (
          'CREATE TABLE suggested_contacts (_id INTEGER PRIMARY KEY, gaia_id '
          'TEXT, chat_id TEXT, name TEXT, first_name TEXT, packed_circle_ids '
          'TEXT, profile_photo_url TEXT, sequence INT, suggestion_type INT, '
          'logging_id TEXT, affinity_score REAL DEFAULT (0.0), '
          'is_in_same_domain INT DEFAULT (0))')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a POSIX time in microseconds date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTimeInMicroseconds: date and time value or None if not
          available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp)

  def ParseMessagesRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses an Messages row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidHangoutsMessageData()
    event_data.body = self._GetRowValue(query_hash, row, 'text')
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')
    event_data.message_status = self._GetRowValue(query_hash, row, 'status')
    event_data.message_type = self._GetRowValue(query_hash, row, 'type')
    event_data.offset = self._GetRowValue(query_hash, row, '_id')
    event_data.query = query
    event_data.sender = self._GetRowValue(query_hash, row, 'full_name')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidHangoutsMessagePlugin)
