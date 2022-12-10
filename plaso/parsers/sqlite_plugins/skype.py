# -*- coding: utf-8 -*-
"""SQLite parser plugin for Skype database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class SkypeAccountEventData(events.EventData):
  """Skype account event data.

  Attributes:
    authentication_request_time (dfdatetime.DateTimeValues): date and time
         the account was last requested to authenticate.
    authentication_request_sent_time (dfdatetime.DateTimeValues): date and time
         the last authentication request was sent.
    country (str): home country of the account holder.
    display_name (str): display name of the account holder.
    email (str): registered email address of the account holder.
    last_online_time (dfdatetime.DateTimeValues): date and time the account
         was last online.
    last_used_time (dfdatetime.DateTimeValues): date and time the account
         was last used.
    mood_change_time (dfdatetime.DateTimeValues): date and time the mood was
        last changed.
    offset (str): identifier of the row, from which the event data was
        extracted.
    profile_change_time (dfdatetime.DateTimeValues): date and time the profile
         was last changed.
    query (str): SQL query that was used to obtain the event data.
    username (str): full name of the Skype account holder and display name.
  """

  DATA_TYPE = 'skype:event:account'

  def __init__(self):
    """Initialize event data."""
    super(SkypeAccountEventData, self).__init__(data_type=self.DATA_TYPE)
    self.authentication_request_time = None
    self.authentication_request_sent_time = None
    self.country = None
    self.display_name = None
    self.email = None
    self.last_online_time = None
    self.last_used_time = None
    self.mood_change_time = None
    self.offset = None
    self.profile_change_time = None
    self.query = None
    self.username = None


class SkypeCallEventData(events.EventData):
  """Skype call event data.

  Attributes:
    attempt_time (dfdatetime.DateTimeValues): date and time the call was
        attempted.
    call_type (str): call type, such as: WAITING, STARTED, FINISHED.
    dst_call (str): account which received the call.
    duration (int): number of seconds the call lasted.
    end_time (dfdatetime.DateTimeValues): date and time the call was stopped.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    src_call (str): account which started the call.
    start_time (dfdatetime.DateTimeValues): date and time the call was started.
    user_start_call (bool): True if the owner account started the call.
    video_conference (bool): True if the call was a video conference.
  """

  DATA_TYPE = 'skype:event:call'

  def __init__(self):
    """Initialize event data."""
    super(SkypeCallEventData, self).__init__(data_type=self.DATA_TYPE)
    self.attempt_time = None
    self.call_type = None
    self.dst_call = None
    self.duration = None
    self.end_time = None
    self.offset = None
    self.query = None
    self.src_call = None
    self.start_time = None
    self.user_start_call = None
    self.video_conference = None


class SkypeChatEventData(events.EventData):
  """Skype chat event data.

  Attributes:
    from_account (str): from display name and the author.
    query (str): SQL query that was used to obtain the event data.
    recorded_time (dfdatetime.DateTimeValues): date and time the chat
        was recorded.
    text (str): body XML.
    title (str): title.
    to_account (str): accounts, excluding the author, of the conversation.
  """

  DATA_TYPE = 'skype:event:chat'

  def __init__(self):
    """Initializes event data."""
    super(SkypeChatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.from_account = None
    self.query = None
    self.recorded_time = None
    self.text = None
    self.title = None
    self.to_account = None


class SkypeSMSEventData(events.EventData):
  """Skype SMS event data.

  Attributes:
    number (str): phone number where the SMS was sent.
    query (str): SQL query that was used to obtain the event data.
    recorded_time (dfdatetime.DateTimeValues): date and time the SMS
        was recorded.
    text (str): text (SMS body) that was sent.
  """

  DATA_TYPE = 'skype:event:sms'

  def __init__(self):
    """Initialize event data."""
    super(SkypeSMSEventData, self).__init__(data_type=self.DATA_TYPE)
    self.number = None
    self.query = None
    self.recorded_time = None
    self.text = None


class SkypeTransferFileEventData(events.EventData):
  """Skype file transfer event data.

  Attributes:
    accept_time (dfdatetime.DateTimeValues): date and time the file transfer was
        accepted.
    destination (str): account that received the file.
    end_time (dfdatetime.DateTimeValues): date and time the file transfer was
        stopped.
    offset (str): identifier of the row, from which the event data was
        extracted.
    query (str): SQL query that was used to obtain the event data.
    source (str): account that sent the file.
    start_time (dfdatetime.DateTimeValues): date and time the file transfer was
        started.
    transfer_status (int): file transfer status.
    transferred_filename (str): name of the file transferred.
    transferred_filepath (str): path of the file transferred.
    transferred_filesize (int): size of the file transferred.
  """

  DATA_TYPE = 'skype:event:transferfile'

  def __init__(self):
    """Initialize event data."""
    super(SkypeTransferFileEventData, self).__init__(data_type=self.DATA_TYPE)
    self.accept_time = None
    self.destination = None
    self.end_time = None
    self.offset = None
    self.query = None
    self.source = None
    self.start_time = None
    self.transfer_status = None
    self.transferred_filename = None
    self.transferred_filepath = None
    self.transferred_filesize = None


class SkypePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Skype database files."""

  NAME = 'skype'
  DATA_FORMAT = 'Skype SQLite database (main.db) file'

  REQUIRED_STRUCTURE = {
      'Accounts': frozenset([
          'id', 'fullname', 'given_displayname', 'emails', 'country',
          'profile_timestamp', 'authreq_timestamp', 'lastonline_timestamp',
          'mood_timestamp', 'sent_authrequest_time']),
      'Calls': frozenset([
          'id', 'is_incoming', 'begin_timestamp']),
      'CallMembers': frozenset([
          'guid', 'call_db_id', 'videostatus', 'start_timestamp',
          'call_duration']),
      'Chats': frozenset([
          'id', 'participants', 'friendlyname', 'dialog_partner', 'name']),
      'Messages': frozenset([
          'author', 'from_dispname', 'body_xml', 'timestamp', 'chatname']),
      'SMSes': frozenset([
          'id', 'target_numbers', 'timestamp', 'body']),
      'Transfers': frozenset([
          'parent_id', 'partner_handle', 'partner_dispname', 'pk_id', 'id',
          'offer_send_list', 'starttime', 'accepttime', 'finishtime',
          'filepath', 'filename', 'filesize', 'status'])}

  # Queries for building cache.
  QUERY_DEST_FROM_TRANSFER = (
      'SELECT parent_id, partner_handle AS skypeid, '
      'partner_dispname AS skypename FROM transfers')
  QUERY_SOURCE_FROM_TRANSFER = (
      'SELECT pk_id, partner_handle AS skypeid, '
      'partner_dispname AS skypename FROM transfers')

  QUERIES = [
      (('SELECT c.id, c.participants, c.friendlyname AS title, '
        'm.author AS author, m.from_dispname AS from_displayname, '
        'm.body_xml, m.timestamp, c.dialog_partner FROM Chats c, Messages m '
        'WHERE c.name = m.chatname'), 'ParseChat'),
      (('SELECT id, fullname, given_displayname, emails, '
        'country, profile_timestamp, authreq_timestamp, '
        'lastonline_timestamp, mood_timestamp, sent_authrequest_time, '
        'lastused_timestamp FROM Accounts'), 'ParseAccountInformation'),
      (('SELECT id, target_numbers AS dstnum_sms, timestamp AS time_sms, '
        'body AS msg_sms FROM SMSes'), 'ParseSMS'),
      (('SELECT id, partner_handle, partner_dispname, offer_send_list, '
        'starttime, accepttime, finishtime, filepath, filename, filesize, '
        'status, parent_id, pk_id FROM Transfers'), 'ParseFileTransfer'),
      (('SELECT c.id, cm.guid, c.is_incoming, '
        'cm.call_db_id, cm.videostatus, c.begin_timestamp AS try_call, '
        'cm.start_timestamp AS accept_call, cm.call_duration '
        'FROM Calls c, CallMembers cm '
        'WHERE c.id = cm.call_db_id;'), 'ParseCall')]

  SCHEMAS = [{
      'Accounts': (
          'CREATE TABLE Accounts (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, status INTEGER, pwdchangestatus INTEGER, '
          'logoutreason INTEGER, commitstatus INTEGER, suggested_skypename '
          'TEXT, skypeout_balance_currency TEXT, skypeout_balance INTEGER, '
          'skypeout_precision INTEGER, skypein_numbers TEXT, subscriptions '
          'TEXT, cblsyncstatus INTEGER, offline_callforward TEXT, chat_policy '
          'INTEGER, skype_call_policy INTEGER, pstn_call_policy INTEGER, '
          'avatar_policy INTEGER, buddycount_policy INTEGER, timezone_policy '
          'INTEGER, webpresence_policy INTEGER, phonenumbers_policy INTEGER, '
          'voicemail_policy INTEGER, authrequest_policy INTEGER, ad_policy '
          'INTEGER, partner_optedout TEXT, service_provider_info TEXT, '
          'registration_timestamp INTEGER, nr_of_other_instances INTEGER, '
          'partner_channel_status TEXT, flamingo_xmpp_status INTEGER, '
          'federated_presence_policy INTEGER, liveid_membername TEXT, '
          'roaming_history_enabled INTEGER, cobrand_id INTEGER, '
          'owner_under_legal_age INTEGER, type INTEGER, skypename TEXT, '
          'pstnnumber TEXT, fullname TEXT, birthday INTEGER, gender INTEGER, '
          'languages TEXT, country TEXT, province TEXT, city TEXT, phone_home '
          'TEXT, phone_office TEXT, phone_mobile TEXT, emails TEXT, homepage '
          'TEXT, about TEXT, profile_timestamp INTEGER, received_authrequest '
          'TEXT, displayname TEXT, refreshing INTEGER, given_authlevel '
          'INTEGER, aliases TEXT, authreq_timestamp INTEGER, mood_text TEXT, '
          'timezone INTEGER, nrof_authed_buddies INTEGER, ipcountry TEXT, '
          'given_displayname TEXT, availability INTEGER, lastonline_timestamp '
          'INTEGER, capabilities BLOB, avatar_image BLOB, assigned_speeddial '
          'TEXT, lastused_timestamp INTEGER, authrequest_count INTEGER, '
          'assigned_comment TEXT, alertstring TEXT, avatar_timestamp INTEGER, '
          'mood_timestamp INTEGER, rich_mood_text TEXT, synced_email BLOB, '
          'set_availability INTEGER, options_change_future BLOB, '
          'cbl_profile_blob BLOB, authorized_time INTEGER, sent_authrequest '
          'TEXT, sent_authrequest_time INTEGER, sent_authrequest_serial '
          'INTEGER, buddyblob BLOB, cbl_future BLOB, node_capabilities '
          'INTEGER, node_capabilities_and INTEGER, revoked_auth INTEGER, '
          'added_in_shared_group INTEGER, in_shared_group INTEGER, '
          'authreq_history BLOB, profile_attachments BLOB, stack_version '
          'INTEGER, offline_authreq_id INTEGER, verified_email BLOB, '
          'verified_company BLOB, uses_jcs INTEGER)'),
      'Alerts': (
          'CREATE TABLE Alerts (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
          'INTEGER, timestamp INTEGER, partner_name TEXT, is_unseen INTEGER, '
          'partner_id INTEGER, partner_event TEXT, partner_history TEXT, '
          'partner_header TEXT, partner_logo TEXT, meta_expiry INTEGER, '
          'message_header_caption TEXT, message_header_title TEXT, '
          'message_header_subject TEXT, message_header_cancel TEXT, '
          'message_header_later TEXT, message_content TEXT, message_footer '
          'TEXT, message_button_caption TEXT, message_button_uri TEXT, '
          'message_type INTEGER, window_size INTEGER, chatmsg_guid BLOB, '
          'notification_id INTEGER, event_flags INTEGER, '
          'extprop_hide_from_history INTEGER)'),
      'AppSchemaVersion': (
          'CREATE TABLE AppSchemaVersion (ClientVersion TEXT NOT NULL, '
          'SQLiteSchemaVersion INTEGER NOT NULL, SchemaUpdateType INTEGER NOT '
          'NULL)'),
      'CallMembers': (
          'CREATE TABLE CallMembers (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, identity TEXT, dispname TEXT, languages '
          'TEXT, call_duration INTEGER, price_per_minute INTEGER, '
          'price_precision INTEGER, price_currency TEXT, payment_category '
          'TEXT, type INTEGER, status INTEGER, failurereason INTEGER, '
          'sounderror_code INTEGER, soundlevel INTEGER, pstn_statustext TEXT, '
          'pstn_feedback TEXT, forward_targets TEXT, forwarded_by TEXT, '
          'debuginfo TEXT, videostatus INTEGER, target_identity TEXT, '
          'mike_status INTEGER, is_read_only INTEGER, quality_status INTEGER, '
          'call_name TEXT, transfer_status INTEGER, transfer_active INTEGER, '
          'transferred_by TEXT, transferred_to TEXT, guid TEXT, '
          'next_redial_time INTEGER, nrof_redials_done INTEGER, '
          'nrof_redials_left INTEGER, transfer_topic TEXT, real_identity '
          'TEXT, start_timestamp INTEGER, is_conference INTEGER, '
          'quality_problems TEXT, identity_type INTEGER, country TEXT, '
          'creation_timestamp INTEGER, stats_xml TEXT, '
          'is_premium_video_sponsor INTEGER, is_multiparty_video_capable '
          'INTEGER, recovery_in_progress INTEGER, nonse_word TEXT, '
          'nr_of_delivered_push_notifications INTEGER, call_session_guid '
          'TEXT, version_string TEXT, pk_status INTEGER, call_db_id INTEGER, '
          'prime_status INTEGER)'),
      'Calls': (
          'CREATE TABLE Calls (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
          'INTEGER, begin_timestamp INTEGER, topic TEXT, is_muted INTEGER, '
          'is_unseen_missed INTEGER, host_identity TEXT, mike_status INTEGER, '
          'duration INTEGER, soundlevel INTEGER, access_token TEXT, '
          'active_members INTEGER, is_active INTEGER, name TEXT, '
          'video_disabled INTEGER, joined_existing INTEGER, server_identity '
          'TEXT, vaa_input_status INTEGER, is_incoming INTEGER, is_conference '
          'INTEGER, is_on_hold INTEGER, start_timestamp INTEGER, '
          'quality_problems TEXT, current_video_audience TEXT, '
          'premium_video_status INTEGER, premium_video_is_grace_period '
          'INTEGER, is_premium_video_sponsor INTEGER, '
          'premium_video_sponsor_list TEXT, old_members BLOB, partner_handle '
          'TEXT, partner_dispname TEXT, type INTEGER, status INTEGER, '
          'failurereason INTEGER, failurecode INTEGER, pstn_number TEXT, '
          'old_duration INTEGER, conf_participants BLOB, pstn_status TEXT, '
          'members BLOB, conv_dbid INTEGER)'),
      'ChatMembers': (
          'CREATE TABLE ChatMembers (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, chatname TEXT, identity TEXT, role INTEGER, '
          'is_active INTEGER, cur_activities INTEGER, adder TEXT)'),
      'Chats': (
          'CREATE TABLE Chats (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
          'INTEGER, name TEXT, options INTEGER, friendlyname TEXT, '
          'description TEXT, timestamp INTEGER, activity_timestamp INTEGER, '
          'dialog_partner TEXT, adder TEXT, type INTEGER, mystatus INTEGER, '
          'myrole INTEGER, posters TEXT, participants TEXT, applicants TEXT, '
          'banned_users TEXT, name_text TEXT, topic TEXT, topic_xml TEXT, '
          'guidelines TEXT, picture BLOB, alertstring TEXT, is_bookmarked '
          'INTEGER, passwordhint TEXT, unconsumed_suppressed_msg INTEGER, '
          'unconsumed_normal_msg INTEGER, unconsumed_elevated_msg INTEGER, '
          'unconsumed_msg_voice INTEGER, activemembers TEXT, state_data BLOB, '
          'lifesigns INTEGER, last_change INTEGER, first_unread_message '
          'INTEGER, pk_type INTEGER, dbpath TEXT, split_friendlyname TEXT, '
          'conv_dbid INTEGER)'),
      'ContactGroups': (
          'CREATE TABLE ContactGroups (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, type INTEGER, custom_group_id INTEGER, '
          'given_displayname TEXT, nrofcontacts INTEGER, nrofcontacts_online '
          'INTEGER, given_sortorder INTEGER, type_old INTEGER, proposer TEXT, '
          'description TEXT, associated_chat TEXT, members TEXT, cbl_id '
          'INTEGER, cbl_blob BLOB, fixed INTEGER, keep_sharedgroup_contacts '
          'INTEGER, chats TEXT, extprop_is_hidden INTEGER, '
          'extprop_sortorder_value INTEGER, extprop_is_expanded INTEGER)'),
      'Contacts': (
          'CREATE TABLE Contacts (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, type INTEGER, skypename TEXT, pstnnumber '
          'TEXT, aliases TEXT, fullname TEXT, birthday INTEGER, gender '
          'INTEGER, languages TEXT, country TEXT, province TEXT, city TEXT, '
          'phone_home TEXT, phone_office TEXT, phone_mobile TEXT, emails '
          'TEXT, hashed_emails TEXT, homepage TEXT, about TEXT, avatar_image '
          'BLOB, mood_text TEXT, rich_mood_text TEXT, timezone INTEGER, '
          'capabilities BLOB, profile_timestamp INTEGER, nrof_authed_buddies '
          'INTEGER, ipcountry TEXT, avatar_timestamp INTEGER, mood_timestamp '
          'INTEGER, received_authrequest TEXT, authreq_timestamp INTEGER, '
          'lastonline_timestamp INTEGER, availability INTEGER, displayname '
          'TEXT, refreshing INTEGER, given_authlevel INTEGER, '
          'given_displayname TEXT, assigned_speeddial TEXT, assigned_comment '
          'TEXT, alertstring TEXT, lastused_timestamp INTEGER, '
          'authrequest_count INTEGER, assigned_phone1 TEXT, '
          'assigned_phone1_label TEXT, assigned_phone2 TEXT, '
          'assigned_phone2_label TEXT, assigned_phone3 TEXT, '
          'assigned_phone3_label TEXT, buddystatus INTEGER, isauthorized '
          'INTEGER, popularity_ord INTEGER, external_id TEXT, '
          'external_system_id TEXT, isblocked INTEGER, '
          'authorization_certificate BLOB, certificate_send_count INTEGER, '
          'account_modification_serial_nr INTEGER, saved_directory_blob BLOB, '
          'nr_of_buddies INTEGER, server_synced INTEGER, contactlist_track '
          'INTEGER, last_used_networktime INTEGER, authorized_time INTEGER, '
          'sent_authrequest TEXT, sent_authrequest_time INTEGER, '
          'sent_authrequest_serial INTEGER, buddyblob BLOB, cbl_future BLOB, '
          'node_capabilities INTEGER, revoked_auth INTEGER, '
          'added_in_shared_group INTEGER, in_shared_group INTEGER, '
          'authreq_history BLOB, profile_attachments BLOB, stack_version '
          'INTEGER, offline_authreq_id INTEGER, node_capabilities_and '
          'INTEGER, authreq_crc INTEGER, authreq_src INTEGER, pop_score '
          'INTEGER, authreq_nodeinfo BLOB, main_phone TEXT, unified_servants '
          'TEXT, phone_home_normalized TEXT, phone_office_normalized TEXT, '
          'phone_mobile_normalized TEXT, sent_authrequest_initmethod INTEGER, '
          'authreq_initmethod INTEGER, verified_email BLOB, verified_company '
          'BLOB, sent_authrequest_extrasbitmask INTEGER, liveid_cid TEXT, '
          'extprop_seen_birthday INTEGER, extprop_sms_target INTEGER, '
          'extprop_external_data TEXT, extprop_must_hide_avatar INTEGER)'),
      'Conversations': (
          'CREATE TABLE Conversations (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, identity TEXT, type INTEGER, live_host TEXT, '
          'live_start_timestamp INTEGER, live_is_muted INTEGER, alert_string '
          'TEXT, is_bookmarked INTEGER, given_displayname TEXT, displayname '
          'TEXT, local_livestatus INTEGER, inbox_timestamp INTEGER, '
          'inbox_message_id INTEGER, unconsumed_suppressed_messages INTEGER, '
          'unconsumed_normal_messages INTEGER, unconsumed_elevated_messages '
          'INTEGER, unconsumed_messages_voice INTEGER, active_vm_id INTEGER, '
          'context_horizon INTEGER, consumption_horizon INTEGER, '
          'last_activity_timestamp INTEGER, active_invoice_message INTEGER, '
          'spawned_from_convo_id INTEGER, pinned_order INTEGER, creator TEXT, '
          'creation_timestamp INTEGER, my_status INTEGER, opt_joining_enabled '
          'INTEGER, opt_access_token TEXT, opt_entry_level_rank INTEGER, '
          'opt_disclose_history INTEGER, opt_history_limit_in_days INTEGER, '
          'opt_admin_only_activities INTEGER, passwordhint TEXT, meta_name '
          'TEXT, meta_topic TEXT, meta_guidelines TEXT, meta_picture BLOB, '
          'picture TEXT, is_p2p_migrated INTEGER, premium_video_status '
          'INTEGER, premium_video_is_grace_period INTEGER, guid TEXT, '
          'dialog_partner TEXT, meta_description TEXT, '
          'premium_video_sponsor_list TEXT, mcr_caller TEXT, chat_dbid '
          'INTEGER, history_horizon INTEGER, history_sync_state TEXT, '
          'thread_version TEXT, consumption_horizon_set_at INTEGER, '
          'alt_identity TEXT, extprop_profile_height INTEGER, '
          'extprop_chat_width INTEGER, extprop_chat_left_margin INTEGER, '
          'extprop_chat_right_margin INTEGER, extprop_entry_height INTEGER, '
          'extprop_windowpos_x INTEGER, extprop_windowpos_y INTEGER, '
          'extprop_windowpos_w INTEGER, extprop_windowpos_h INTEGER, '
          'extprop_window_maximized INTEGER, extprop_window_detached INTEGER, '
          'extprop_pinned_order INTEGER, extprop_new_in_inbox INTEGER, '
          'extprop_tab_order INTEGER, extprop_video_layout INTEGER, '
          'extprop_video_chat_height INTEGER, extprop_chat_avatar INTEGER, '
          'extprop_consumption_timestamp INTEGER, extprop_form_visible '
          'INTEGER, extprop_recovery_mode INTEGER)'),
      'DbMeta': (
          'CREATE TABLE DbMeta (key TEXT NOT NULL PRIMARY KEY, value TEXT)'),
      'LegacyMessages': (
          'CREATE TABLE LegacyMessages (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER)'),
      'Messages': (
          'CREATE TABLE Messages (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, convo_id INTEGER, chatname TEXT, author '
          'TEXT, from_dispname TEXT, author_was_live INTEGER, guid BLOB, '
          'dialog_partner TEXT, timestamp INTEGER, type INTEGER, '
          'sending_status INTEGER, consumption_status INTEGER, edited_by '
          'TEXT, edited_timestamp INTEGER, param_key INTEGER, param_value '
          'INTEGER, body_xml TEXT, identities TEXT, reason TEXT, leavereason '
          'INTEGER, participant_count INTEGER, error_code INTEGER, '
          'chatmsg_type INTEGER, chatmsg_status INTEGER, body_is_rawxml '
          'INTEGER, oldoptions INTEGER, newoptions INTEGER, newrole INTEGER, '
          'pk_id INTEGER, crc INTEGER, remote_id INTEGER, call_guid TEXT, '
          'extprop_contact_review_date TEXT, extprop_contact_received_stamp '
          'INTEGER, extprop_contact_reviewed INTEGER)'),
      'Participants': (
          'CREATE TABLE Participants (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, convo_id INTEGER, identity TEXT, rank '
          'INTEGER, requested_rank INTEGER, text_status INTEGER, voice_status '
          'INTEGER, video_status INTEGER, live_identity TEXT, '
          'live_price_for_me TEXT, live_fwd_identities TEXT, '
          'live_start_timestamp INTEGER, sound_level INTEGER, debuginfo TEXT, '
          'next_redial_time INTEGER, nrof_redials_left INTEGER, '
          'last_voice_error TEXT, quality_problems TEXT, live_type INTEGER, '
          'live_country TEXT, transferred_by TEXT, transferred_to TEXT, adder '
          'TEXT, last_leavereason INTEGER, is_premium_video_sponsor INTEGER, '
          'is_multiparty_video_capable INTEGER, live_identity_to_use TEXT, '
          'livesession_recovery_in_progress INTEGER, '
          'is_multiparty_video_updatable INTEGER, real_identity TEXT, '
          'extprop_default_identity INTEGER)'),
      'SMSes': (
          'CREATE TABLE SMSes (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
          'INTEGER, type INTEGER, outgoing_reply_type INTEGER, status '
          'INTEGER, failurereason INTEGER, is_failed_unseen INTEGER, '
          'timestamp INTEGER, price INTEGER, price_precision INTEGER, '
          'price_currency TEXT, reply_to_number TEXT, target_numbers TEXT, '
          'target_statuses BLOB, body TEXT, chatmsg_id INTEGER, identity '
          'TEXT, notification_id INTEGER, event_flags INTEGER, '
          'reply_id_number TEXT, convo_name TEXT, extprop_hide_from_history '
          'INTEGER, extprop_extended INTEGER)'),
      'Transfers': (
          'CREATE TABLE Transfers (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, type INTEGER, partner_handle TEXT, '
          'partner_dispname TEXT, status INTEGER, failurereason INTEGER, '
          'starttime INTEGER, finishtime INTEGER, filepath TEXT, filename '
          'TEXT, filesize TEXT, bytestransferred TEXT, bytespersecond '
          'INTEGER, chatmsg_guid BLOB, chatmsg_index INTEGER, convo_id '
          'INTEGER, pk_id INTEGER, nodeid BLOB, last_activity INTEGER, flags '
          'INTEGER, old_status INTEGER, old_filepath INTEGER, accepttime '
          'INTEGER, parent_id INTEGER, offer_send_list TEXT, '
          'extprop_localfilename TEXT, extprop_hide_from_history INTEGER, '
          'extprop_window_visible INTEGER, extprop_handled_by_chat INTEGER)'),
      'VideoMessages': (
          'CREATE TABLE VideoMessages (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, qik_id BLOB, attached_msg_ids TEXT, '
          'sharing_id TEXT, status INTEGER, vod_status INTEGER, vod_path '
          'TEXT, local_path TEXT, public_link TEXT, progress INTEGER, title '
          'TEXT, description TEXT, author TEXT, creation_timestamp INTEGER)'),
      'Videos': (
          'CREATE TABLE Videos (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
          'INTEGER, status INTEGER, error TEXT, debuginfo TEXT, dimensions '
          'TEXT, media_type INTEGER, duration_1080 INTEGER, duration_720 '
          'INTEGER, duration_hqv INTEGER, duration_vgad2 INTEGER, '
          'duration_ltvgad2 INTEGER, timestamp INTEGER, hq_present INTEGER, '
          'duration_ss INTEGER, ss_timestamp INTEGER, convo_id INTEGER, '
          'device_path TEXT)'),
      'Voicemails': (
          'CREATE TABLE Voicemails (id INTEGER NOT NULL PRIMARY KEY, '
          'is_permanent INTEGER, type INTEGER, partner_handle TEXT, '
          'partner_dispname TEXT, status INTEGER, failurereason INTEGER, '
          'subject TEXT, timestamp INTEGER, duration INTEGER, '
          'allowed_duration INTEGER, playback_progress INTEGER, convo_id '
          'INTEGER, chatmsg_guid BLOB, notification_id INTEGER, flags '
          'INTEGER, size INTEGER, path TEXT, failures INTEGER, vflags '
          'INTEGER, xmsg TEXT, extprop_hide_from_history INTEGER)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def ParseAccountInformation(
      self, parser_mediator, query, row, **unused_kwargs):
    """Parses account information.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row with account information.
    """
    query_hash = hash(query)

    display_name = self._GetRowValue(query_hash, row, 'given_displayname')
    fullname = self._GetRowValue(query_hash, row, 'fullname')

    # TODO: Move this to the formatter, and ensure username is rendered
    # properly when fullname and/or display_name is None.
    username = '{0!s} <{1!s}>'.format(fullname, display_name)

    event_data = SkypeAccountEventData()
    event_data.authentication_request_time = self._GetDateTimeRowValue(
        query_hash, row, 'authreq_timestamp')
    event_data.authentication_request_sent_time = self._GetDateTimeRowValue(
        query_hash, row, 'sent_authrequest_time')
    event_data.country = self._GetRowValue(query_hash, row, 'country')
    event_data.display_name = display_name
    event_data.email = self._GetRowValue(query_hash, row, 'emails')
    event_data.last_online_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastonline_timestamp')
    event_data.last_used_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastused_timestamp')
    event_data.mood_change_time = self._GetDateTimeRowValue(
        query_hash, row, 'mood_timestamp')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.profile_change_time = self._GetDateTimeRowValue(
        query_hash, row, 'profile_timestamp')
    event_data.query = query
    event_data.username = username

    parser_mediator.ProduceEventData(event_data)

  def ParseCall(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a call.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
      query (Optional[str]): query.
    """
    query_hash = hash(query)

    guid = self._GetRowValue(query_hash, row, 'guid')
    is_incoming = self._GetRowValue(query_hash, row, 'is_incoming')
    videostatus = self._GetRowValue(query_hash, row, 'videostatus')

    try:
      aux = guid
      if aux:
        aux_list = aux.split('-')
        src_aux = aux_list[0]
        dst_aux = aux_list[1]
      else:
        src_aux = 'Unknown [no GUID]'
        dst_aux = 'Unknown [no GUID]'
    except IndexError:
      src_aux = 'Unknown [{0:s}]'.format(guid)
      dst_aux = 'Unknown [{0:s}]'.format(guid)

    if is_incoming == '0':
      user_start_call = True
      source = src_aux

      ip_address = self._GetRowValue(query_hash, row, 'ip_address')
      if ip_address:
        destination = '{0:s} <{1:s}>'.format(dst_aux, ip_address)
      else:
        destination = dst_aux
    else:
      user_start_call = False
      source = src_aux
      destination = dst_aux

    call_identifier = self._GetRowValue(query_hash, row, 'id')
    call_duration = self._GetRowValue(query_hash, row, 'call_duration')

    event_data = SkypeCallEventData()
    event_data.attempt_time = self._GetDateTimeRowValue(
        query_hash, row, 'try_call')
    event_data.call_type = 'WAITING'
    event_data.dst_call = destination
    event_data.duration = call_duration
    event_data.offset = call_identifier
    event_data.query = query
    event_data.src_call = source
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'accept_call')
    event_data.user_start_call = user_start_call
    event_data.video_conference = videostatus == '3'

    start_timestamp = self._GetRowValue(query_hash, row, 'accept_call')
    if start_timestamp and call_duration:
      event_data.call_type = 'ACCEPTED'
      event_data.end_time = dfdatetime_posix_time.PosixTime(
          timestamp=start_timestamp + call_duration)

    parser_mediator.ProduceEventData(event_data)

  def ParseChat(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a chat message.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    participants = self._GetRowValue(query_hash, row, 'participants')
    author = self._GetRowValue(query_hash, row, 'author')
    dialog_partner = self._GetRowValue(query_hash, row, 'dialog_partner')
    from_displayname = self._GetRowValue(query_hash, row, 'from_displayname')

    accounts = []
    participants = participants.split(' ')
    for participant in participants:
      if participant != author:
        accounts.append(participant)

    to_account = ', '.join(accounts)
    if not to_account:
      to_account = dialog_partner or 'Unknown User'

    from_account = '{0:s} <{1:s}>'.format(from_displayname, author)

    event_data = SkypeChatEventData()
    event_data.from_account = from_account
    event_data.query = query
    event_data.recorded_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')
    event_data.text = self._GetRowValue(query_hash, row, 'body_xml')
    event_data.title = self._GetRowValue(query_hash, row, 'title')
    event_data.to_account = to_account

    parser_mediator.ProduceEventData(event_data)

  def ParseFileTransfer(
      self, parser_mediator, query, row, cache=None, database=None,
      **unused_kwargs):
    """Parses a file transfer.

    There is no direct relationship between who sends the file and
    who accepts the file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
      cache (Optional[SQLiteCache]): cache.
      database (Optional[SQLiteDatabase]): database.
    """
    query_hash = hash(query)

    source_dict = cache.GetResults('source')
    if not source_dict:
      results = database.Query(self.QUERY_SOURCE_FROM_TRANSFER)

      cache.CacheQueryResults(
          results, 'source', 'pk_id', ('skypeid', 'skypename'))
      source_dict = cache.GetResults('source')

    dest_dict = cache.GetResults('destination')
    if not dest_dict:
      results = database.Query(self.QUERY_DEST_FROM_TRANSFER)

      cache.CacheQueryResults(
          results, 'destination', 'parent_id', ('skypeid', 'skypename'))
      dest_dict = cache.GetResults('destination')

    source = 'Unknown'
    destination = 'Unknown'

    parent_id = self._GetRowValue(query_hash, row, 'parent_id')
    partner_dispname = self._GetRowValue(query_hash, row, 'partner_dispname')
    partner_handle = self._GetRowValue(query_hash, row, 'partner_handle')

    if parent_id:
      destination = '{0:s} <{1:s}>'.format(partner_handle, partner_dispname)
      skype_id, skype_name = source_dict.get(parent_id, [None, None])
      if skype_name:
        source = '{0:s} <{1:s}>'.format(skype_id, skype_name)
    else:
      source = '{0:s} <{1:s}>'.format(partner_handle, partner_dispname)

      pk_id = self._GetRowValue(query_hash, row, 'pk_id')
      if pk_id:
        skype_id, skype_name = dest_dict.get(pk_id, [None, None])
        if skype_name:
          destination = '{0:s} <{1:s}>'.format(skype_id, skype_name)

    filename = self._GetRowValue(query_hash, row, 'filename')
    filesize = self._GetRowValue(query_hash, row, 'filesize')

    try:
      file_size = int(filesize, 10)
    except (ValueError, TypeError):
      parser_mediator.ProduceExtractionWarning(
          'unable to convert file size: {0!s} of file: {1:s}'.format(
              filesize, filename))
      file_size = 0

    event_data = SkypeTransferFileEventData()
    event_data.accept_time = self._GetDateTimeRowValue(
        query_hash, row, 'accepttime')
    event_data.destination = destination
    event_data.end_time = self._GetDateTimeRowValue(
        query_hash, row, 'finishtime')
    event_data.offset = self._GetRowValue(query_hash, row, 'id')
    event_data.query = query
    event_data.source = source
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'starttime')
    event_data.transfer_status = self._GetRowValue(query_hash, row, 'status')
    event_data.transferred_filename = filename
    event_data.transferred_filepath = self._GetRowValue(
        query_hash, row, 'filepath')
    event_data.transferred_filesize = file_size

    parser_mediator.ProduceEventData(event_data)

  def ParseSMS(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a SMS.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    phone_number = self._GetRowValue(query_hash, row, 'dstnum_sms')
    if phone_number:
      phone_number = phone_number.replace(' ', '')

    event_data = SkypeSMSEventData()
    event_data.number = phone_number
    event_data.query = query
    event_data.recorded_time = self._GetDateTimeRowValue(
        query_hash, row, 'time_sms')
    event_data.text = self._GetRowValue(query_hash, row, 'msg_sms')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(SkypePlugin)
