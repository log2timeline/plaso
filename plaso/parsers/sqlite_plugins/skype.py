# -*- coding: utf-8 -*-
"""This file contains a basic Skype SQLite parser."""

import logging

from plaso.containers import time_events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'Joaquin Moreno Garijo (bastionado@gmail.com)'


class SkypeChatEvent(time_events.PosixTimeEvent):
  """Convenience class for a Skype event.

  Attributes:
    from_account: a string containing the from display name and the author.
    to_account: a string containing the accounts (excluding the
                author) of the conversation.
    text: a string containing the body XML.
    title: a string containing the title.
  """

  DATA_TYPE = u'skype:event:chat'

  def __init__(
      self, posix_time, from_displayname, author, to_account, title, body_xml):
    """Build a Skype Event from a single row.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      from_displayname: a string containing the from display name.
      author: a string containing the author.
      to_account: a string containing the accounts (excluding the
                  author) of the conversation.
      title: a string containing the title.
      body_xml: a string containing the body XML.
    """
    super(SkypeChatEvent, self).__init__(posix_time, u'Chat from Skype')
    self.from_account = u'{0:s} <{1:s}>'.format(from_displayname, author)
    self.text = body_xml
    self.title = title
    self.to_account = to_account


class SkypeAccountEvent(time_events.PosixTimeEvent):
  """Convenience class for account information.

  Attributes:
    country: a string containing the chosen home country of the account
             holder.
    display_name: a string containing the chosen display name of the account
                  holder.
    email: a string containing the registered email address of the account
           holder.
    offset: an integer containing the row identifier.
    username: a string containing the full name of the Skype account holder and
              display name.
  """

  DATA_TYPE = u'skype:event:account'

  def __init__(
      self, posix_time, usage, identifier, full_name, display_name, email,
      country):
    """Initialize the event.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      usage: a string containing the description string of the timestamp.
      identifier: an integer containing the row identifier.
      full_name: a string containing the full name of the Skype account holder.
      display_name: a string containing the chosen display name of the account
                    holder.
      email: a string containing the registered email address of the account
             holder.
      country: a string containing the chosen home country of the account
               holder.
    """
    super(SkypeAccountEvent, self).__init__(posix_time, usage)
    self.country = country
    self.display_name = display_name
    self.email = email
    self.offset = identifier
    self.username = u'{0:s} <{1:s}>'.format(full_name, display_name)


class SkypeSMSEvent(time_events.PosixTimeEvent):
  """Convenience EventObject for SMS.

  Attributes:
    number: a string containing the phone number where the SMS was sent.
    text: a string containing the text (SMS body) that was sent.
  """

  DATA_TYPE = u'skype:event:sms'

  def __init__(self, posix_time, phone_number, text):
    """Read the information related with the SMS.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      phone_number: a string containing the phone number where the SMS was sent.
      text: a string containing the text (SMS body) that was sent.
    """
    super(SkypeSMSEvent, self).__init__(posix_time, u'SMS from Skype')
    self.number = phone_number
    self.text = text


class SkypeCallEvent(time_events.PosixTimeEvent):
  """Convenience EventObject for the calls.

  Attributes:
    call_type: a string containing the call type e.g. WAITING, STARTED,
               FINISHED.
    dst_call: a string containing the account which gets the call.
    src_call: a string containing the account which started the call.
    user_start_call: a boolean which indicates that the owner account
                     started the call.
    video_conference: a boolean which indicates if the call was a video
                      conference.
  """

  DATA_TYPE = u'skype:event:call'

  def __init__(
      self, posix_time, call_type, user_start_call, source, destination,
      video_conference):
    """Contains information if the call was cancelled, accepted or finished.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      call_type: a string containing the call type e.g. WAITING, STARTED,
                 FINISHED.
      user_start_call: a boolean which indicates that the owner account
                       started the call.
      source: a string containing the account which started the call.
      destination: a string containing the account which gets the call.
      video_conference: a boolean which indicates if the call was a video
                        conference.
    """

    super(SkypeCallEvent, self).__init__(posix_time, u'Call from Skype')
    self.call_type = call_type
    self.dst_call = destination
    self.src_call = source
    self.user_start_call = user_start_call
    self.video_conference = video_conference


class SkypeTransferFileEvent(time_events.PosixTimeEvent):
  """Evaluate the action of send a file.

  Attributes:
    action_type: a string containing the action type e.g. GETSOLICITUDE,
                 SENDSOLICITUDE, ACCEPTED, FINISHED.
    destination: a string containing the account that received the file.
    offset: an integer containing the row identifier.
    source: a string containing the account that sent the file.
    transferred_filename: a string containing the name of the file transferred.
    transferred_file_path: a string containing the path of the file transferred.
    transferred_filesize: an integer containing the size of the file
                          transferred.
  """

  DATA_TYPE = u'skype:event:transferfile'

  def __init__(
      self, posix_time, identifier, action_type, source, destination, filename,
      file_path, file_size):
    """Actions related with sending files.

    Args:
      posix_time: the POSIX time value, which contains the number of seconds
                  since January 1, 1970 00:00:00 UTC.
      identifier: an integer containing the row identifier.
      action_type: a string containing the action type e.g. GETSOLICITUDE,
                   SENDSOLICITUDE, ACCEPTED, FINISHED.
      source: a string containing the account that sent the file.
      destination: a string containing the account that received the file.
      filename: a string containing the name of the file transferred.
      file_path: a string containing the path of the file transferred.
      file_size: an integer containing the size of the file transferred.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    super(SkypeTransferFileEvent, self).__init__(
        posix_time, u'File transfer from Skype')
    self.action_type = action_type
    self.destination = destination
    self.offset = identifier
    self.source = source
    self.transferred_filename = filename
    self.transferred_filepath = file_path
    self.transferred_filesize = file_size


class SkypePlugin(interface.SQLitePlugin):
  """SQLite plugin for Skype main.db SQlite database file."""

  NAME = u'skype'
  DESCRIPTION = u'Parser for Skype SQLite database files.'

  # Queries for building cache.
  QUERY_DEST_FROM_TRANSFER = (
      u'SELECT parent_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')
  QUERY_SOURCE_FROM_TRANSFER = (
      u'SELECT pk_id, partner_handle AS skypeid, '
      u'partner_dispname AS skypename FROM transfers')

  # Define the needed queries.
  QUERIES = [
      ((u'SELECT c.id, c.participants, c.friendlyname AS title, '
        u'm.author AS author, m.from_dispname AS from_displayname, '
        u'm.body_xml, m.timestamp, c.dialog_partner FROM Chats c, Messages m '
        u'WHERE c.name = m.chatname'), u'ParseChat'),
      ((u'SELECT id, fullname, given_displayname, emails, '
        u'country, profile_timestamp, authreq_timestamp, '
        u'lastonline_timestamp, mood_timestamp, sent_authrequest_time, '
        u'lastused_timestamp FROM Accounts'), u'ParseAccountInformation'),
      ((u'SELECT id, target_numbers AS dstnum_sms, timestamp AS time_sms, '
        u'body AS msg_sms FROM SMSes'), u'ParseSMS'),
      ((u'SELECT id, partner_handle, partner_dispname, offer_send_list, '
        u'starttime, accepttime, finishtime, filepath, filename, filesize, '
        u'status, parent_id, pk_id FROM Transfers'), u'ParseFileTransfer'),
      ((u'SELECT c.id, cm.guid, c.is_incoming, '
        u'cm.call_db_id, cm.videostatus, c.begin_timestamp AS try_call, '
        u'cm.start_timestamp AS accept_call, cm.call_duration '
        u'FROM Calls c, CallMembers cm '
        u'WHERE c.id = cm.call_db_id;'), u'ParseCall')]

  # The required tables.
  REQUIRED_TABLES = frozenset([
      u'Chats', u'Accounts', u'Conversations', u'Contacts', u'SMSes',
      u'Transfers', u'CallMembers', u'Calls'])

  SCHEMAS = [
      {u'Accounts':
       u'CREATE TABLE Accounts (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, status INTEGER, pwdchangestatus INTEGER, '
       u'logoutreason INTEGER, commitstatus INTEGER, suggested_skypename '
       u'TEXT, skypeout_balance_currency TEXT, skypeout_balance INTEGER, '
       u'skypeout_precision INTEGER, skypein_numbers TEXT, subscriptions '
       u'TEXT, cblsyncstatus INTEGER, offline_callforward TEXT, chat_policy '
       u'INTEGER, skype_call_policy INTEGER, pstn_call_policy INTEGER, '
       u'avatar_policy INTEGER, buddycount_policy INTEGER, timezone_policy '
       u'INTEGER, webpresence_policy INTEGER, phonenumbers_policy INTEGER, '
       u'voicemail_policy INTEGER, authrequest_policy INTEGER, ad_policy '
       u'INTEGER, partner_optedout TEXT, service_provider_info TEXT, '
       u'registration_timestamp INTEGER, nr_of_other_instances INTEGER, '
       u'partner_channel_status TEXT, flamingo_xmpp_status INTEGER, '
       u'federated_presence_policy INTEGER, liveid_membername TEXT, '
       u'roaming_history_enabled INTEGER, cobrand_id INTEGER, '
       u'owner_under_legal_age INTEGER, type INTEGER, skypename TEXT, '
       u'pstnnumber TEXT, fullname TEXT, birthday INTEGER, gender INTEGER, '
       u'languages TEXT, country TEXT, province TEXT, city TEXT, phone_home '
       u'TEXT, phone_office TEXT, phone_mobile TEXT, emails TEXT, homepage '
       u'TEXT, about TEXT, profile_timestamp INTEGER, received_authrequest '
       u'TEXT, displayname TEXT, refreshing INTEGER, given_authlevel '
       u'INTEGER, aliases TEXT, authreq_timestamp INTEGER, mood_text TEXT, '
       u'timezone INTEGER, nrof_authed_buddies INTEGER, ipcountry TEXT, '
       u'given_displayname TEXT, availability INTEGER, lastonline_timestamp '
       u'INTEGER, capabilities BLOB, avatar_image BLOB, assigned_speeddial '
       u'TEXT, lastused_timestamp INTEGER, authrequest_count INTEGER, '
       u'assigned_comment TEXT, alertstring TEXT, avatar_timestamp INTEGER, '
       u'mood_timestamp INTEGER, rich_mood_text TEXT, synced_email BLOB, '
       u'set_availability INTEGER, options_change_future BLOB, '
       u'cbl_profile_blob BLOB, authorized_time INTEGER, sent_authrequest '
       u'TEXT, sent_authrequest_time INTEGER, sent_authrequest_serial '
       u'INTEGER, buddyblob BLOB, cbl_future BLOB, node_capabilities '
       u'INTEGER, node_capabilities_and INTEGER, revoked_auth INTEGER, '
       u'added_in_shared_group INTEGER, in_shared_group INTEGER, '
       u'authreq_history BLOB, profile_attachments BLOB, stack_version '
       u'INTEGER, offline_authreq_id INTEGER, verified_email BLOB, '
       u'verified_company BLOB, uses_jcs INTEGER)',
       u'Alerts':
       u'CREATE TABLE Alerts (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
       u'INTEGER, timestamp INTEGER, partner_name TEXT, is_unseen INTEGER, '
       u'partner_id INTEGER, partner_event TEXT, partner_history TEXT, '
       u'partner_header TEXT, partner_logo TEXT, meta_expiry INTEGER, '
       u'message_header_caption TEXT, message_header_title TEXT, '
       u'message_header_subject TEXT, message_header_cancel TEXT, '
       u'message_header_later TEXT, message_content TEXT, message_footer '
       u'TEXT, message_button_caption TEXT, message_button_uri TEXT, '
       u'message_type INTEGER, window_size INTEGER, chatmsg_guid BLOB, '
       u'notification_id INTEGER, event_flags INTEGER, '
       u'extprop_hide_from_history INTEGER)',
       u'AppSchemaVersion':
       u'CREATE TABLE AppSchemaVersion (ClientVersion TEXT NOT NULL, '
       u'SQLiteSchemaVersion INTEGER NOT NULL, SchemaUpdateType INTEGER NOT '
       u'NULL)',
       u'CallMembers':
       u'CREATE TABLE CallMembers (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, identity TEXT, dispname TEXT, languages TEXT, '
       u'call_duration INTEGER, price_per_minute INTEGER, price_precision '
       u'INTEGER, price_currency TEXT, payment_category TEXT, type INTEGER, '
       u'status INTEGER, failurereason INTEGER, sounderror_code INTEGER, '
       u'soundlevel INTEGER, pstn_statustext TEXT, pstn_feedback TEXT, '
       u'forward_targets TEXT, forwarded_by TEXT, debuginfo TEXT, '
       u'videostatus INTEGER, target_identity TEXT, mike_status INTEGER, '
       u'is_read_only INTEGER, quality_status INTEGER, call_name TEXT, '
       u'transfer_status INTEGER, transfer_active INTEGER, transferred_by '
       u'TEXT, transferred_to TEXT, guid TEXT, next_redial_time INTEGER, '
       u'nrof_redials_done INTEGER, nrof_redials_left INTEGER, '
       u'transfer_topic TEXT, real_identity TEXT, start_timestamp INTEGER, '
       u'is_conference INTEGER, quality_problems TEXT, identity_type '
       u'INTEGER, country TEXT, creation_timestamp INTEGER, stats_xml TEXT, '
       u'is_premium_video_sponsor INTEGER, is_multiparty_video_capable '
       u'INTEGER, recovery_in_progress INTEGER, nonse_word TEXT, '
       u'nr_of_delivered_push_notifications INTEGER, call_session_guid TEXT, '
       u'version_string TEXT, pk_status INTEGER, call_db_id INTEGER, '
       u'prime_status INTEGER)',
       u'Calls':
       u'CREATE TABLE Calls (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
       u'INTEGER, begin_timestamp INTEGER, topic TEXT, is_muted INTEGER, '
       u'is_unseen_missed INTEGER, host_identity TEXT, mike_status INTEGER, '
       u'duration INTEGER, soundlevel INTEGER, access_token TEXT, '
       u'active_members INTEGER, is_active INTEGER, name TEXT, '
       u'video_disabled INTEGER, joined_existing INTEGER, server_identity '
       u'TEXT, vaa_input_status INTEGER, is_incoming INTEGER, is_conference '
       u'INTEGER, is_on_hold INTEGER, start_timestamp INTEGER, '
       u'quality_problems TEXT, current_video_audience TEXT, '
       u'premium_video_status INTEGER, premium_video_is_grace_period '
       u'INTEGER, is_premium_video_sponsor INTEGER, '
       u'premium_video_sponsor_list TEXT, old_members BLOB, partner_handle '
       u'TEXT, partner_dispname TEXT, type INTEGER, status INTEGER, '
       u'failurereason INTEGER, failurecode INTEGER, pstn_number TEXT, '
       u'old_duration INTEGER, conf_participants BLOB, pstn_status TEXT, '
       u'members BLOB, conv_dbid INTEGER)',
       u'ChatMembers':
       u'CREATE TABLE ChatMembers (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, chatname TEXT, identity TEXT, role INTEGER, '
       u'is_active INTEGER, cur_activities INTEGER, adder TEXT)',
       u'Chats':
       u'CREATE TABLE Chats (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
       u'INTEGER, name TEXT, options INTEGER, friendlyname TEXT, description '
       u'TEXT, timestamp INTEGER, activity_timestamp INTEGER, dialog_partner '
       u'TEXT, adder TEXT, type INTEGER, mystatus INTEGER, myrole INTEGER, '
       u'posters TEXT, participants TEXT, applicants TEXT, banned_users '
       u'TEXT, name_text TEXT, topic TEXT, topic_xml TEXT, guidelines TEXT, '
       u'picture BLOB, alertstring TEXT, is_bookmarked INTEGER, passwordhint '
       u'TEXT, unconsumed_suppressed_msg INTEGER, unconsumed_normal_msg '
       u'INTEGER, unconsumed_elevated_msg INTEGER, unconsumed_msg_voice '
       u'INTEGER, activemembers TEXT, state_data BLOB, lifesigns INTEGER, '
       u'last_change INTEGER, first_unread_message INTEGER, pk_type INTEGER, '
       u'dbpath TEXT, split_friendlyname TEXT, conv_dbid INTEGER)',
       u'ContactGroups':
       u'CREATE TABLE ContactGroups (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, type INTEGER, custom_group_id INTEGER, '
       u'given_displayname TEXT, nrofcontacts INTEGER, nrofcontacts_online '
       u'INTEGER, given_sortorder INTEGER, type_old INTEGER, proposer TEXT, '
       u'description TEXT, associated_chat TEXT, members TEXT, cbl_id '
       u'INTEGER, cbl_blob BLOB, fixed INTEGER, keep_sharedgroup_contacts '
       u'INTEGER, chats TEXT, extprop_is_hidden INTEGER, '
       u'extprop_sortorder_value INTEGER, extprop_is_expanded INTEGER)',
       u'Contacts':
       u'CREATE TABLE Contacts (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, type INTEGER, skypename TEXT, pstnnumber '
       u'TEXT, aliases TEXT, fullname TEXT, birthday INTEGER, gender '
       u'INTEGER, languages TEXT, country TEXT, province TEXT, city TEXT, '
       u'phone_home TEXT, phone_office TEXT, phone_mobile TEXT, emails TEXT, '
       u'hashed_emails TEXT, homepage TEXT, about TEXT, avatar_image BLOB, '
       u'mood_text TEXT, rich_mood_text TEXT, timezone INTEGER, capabilities '
       u'BLOB, profile_timestamp INTEGER, nrof_authed_buddies INTEGER, '
       u'ipcountry TEXT, avatar_timestamp INTEGER, mood_timestamp INTEGER, '
       u'received_authrequest TEXT, authreq_timestamp INTEGER, '
       u'lastonline_timestamp INTEGER, availability INTEGER, displayname '
       u'TEXT, refreshing INTEGER, given_authlevel INTEGER, '
       u'given_displayname TEXT, assigned_speeddial TEXT, assigned_comment '
       u'TEXT, alertstring TEXT, lastused_timestamp INTEGER, '
       u'authrequest_count INTEGER, assigned_phone1 TEXT, '
       u'assigned_phone1_label TEXT, assigned_phone2 TEXT, '
       u'assigned_phone2_label TEXT, assigned_phone3 TEXT, '
       u'assigned_phone3_label TEXT, buddystatus INTEGER, isauthorized '
       u'INTEGER, popularity_ord INTEGER, external_id TEXT, '
       u'external_system_id TEXT, isblocked INTEGER, '
       u'authorization_certificate BLOB, certificate_send_count INTEGER, '
       u'account_modification_serial_nr INTEGER, saved_directory_blob BLOB, '
       u'nr_of_buddies INTEGER, server_synced INTEGER, contactlist_track '
       u'INTEGER, last_used_networktime INTEGER, authorized_time INTEGER, '
       u'sent_authrequest TEXT, sent_authrequest_time INTEGER, '
       u'sent_authrequest_serial INTEGER, buddyblob BLOB, cbl_future BLOB, '
       u'node_capabilities INTEGER, revoked_auth INTEGER, '
       u'added_in_shared_group INTEGER, in_shared_group INTEGER, '
       u'authreq_history BLOB, profile_attachments BLOB, stack_version '
       u'INTEGER, offline_authreq_id INTEGER, node_capabilities_and INTEGER, '
       u'authreq_crc INTEGER, authreq_src INTEGER, pop_score INTEGER, '
       u'authreq_nodeinfo BLOB, main_phone TEXT, unified_servants TEXT, '
       u'phone_home_normalized TEXT, phone_office_normalized TEXT, '
       u'phone_mobile_normalized TEXT, sent_authrequest_initmethod INTEGER, '
       u'authreq_initmethod INTEGER, verified_email BLOB, verified_company '
       u'BLOB, sent_authrequest_extrasbitmask INTEGER, liveid_cid TEXT, '
       u'extprop_seen_birthday INTEGER, extprop_sms_target INTEGER, '
       u'extprop_external_data TEXT, extprop_must_hide_avatar INTEGER)',
       u'Conversations':
       u'CREATE TABLE Conversations (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, identity TEXT, type INTEGER, live_host TEXT, '
       u'live_start_timestamp INTEGER, live_is_muted INTEGER, alert_string '
       u'TEXT, is_bookmarked INTEGER, given_displayname TEXT, displayname '
       u'TEXT, local_livestatus INTEGER, inbox_timestamp INTEGER, '
       u'inbox_message_id INTEGER, unconsumed_suppressed_messages INTEGER, '
       u'unconsumed_normal_messages INTEGER, unconsumed_elevated_messages '
       u'INTEGER, unconsumed_messages_voice INTEGER, active_vm_id INTEGER, '
       u'context_horizon INTEGER, consumption_horizon INTEGER, '
       u'last_activity_timestamp INTEGER, active_invoice_message INTEGER, '
       u'spawned_from_convo_id INTEGER, pinned_order INTEGER, creator TEXT, '
       u'creation_timestamp INTEGER, my_status INTEGER, opt_joining_enabled '
       u'INTEGER, opt_access_token TEXT, opt_entry_level_rank INTEGER, '
       u'opt_disclose_history INTEGER, opt_history_limit_in_days INTEGER, '
       u'opt_admin_only_activities INTEGER, passwordhint TEXT, meta_name '
       u'TEXT, meta_topic TEXT, meta_guidelines TEXT, meta_picture BLOB, '
       u'picture TEXT, is_p2p_migrated INTEGER, premium_video_status '
       u'INTEGER, premium_video_is_grace_period INTEGER, guid TEXT, '
       u'dialog_partner TEXT, meta_description TEXT, '
       u'premium_video_sponsor_list TEXT, mcr_caller TEXT, chat_dbid '
       u'INTEGER, history_horizon INTEGER, history_sync_state TEXT, '
       u'thread_version TEXT, consumption_horizon_set_at INTEGER, '
       u'alt_identity TEXT, extprop_profile_height INTEGER, '
       u'extprop_chat_width INTEGER, extprop_chat_left_margin INTEGER, '
       u'extprop_chat_right_margin INTEGER, extprop_entry_height INTEGER, '
       u'extprop_windowpos_x INTEGER, extprop_windowpos_y INTEGER, '
       u'extprop_windowpos_w INTEGER, extprop_windowpos_h INTEGER, '
       u'extprop_window_maximized INTEGER, extprop_window_detached INTEGER, '
       u'extprop_pinned_order INTEGER, extprop_new_in_inbox INTEGER, '
       u'extprop_tab_order INTEGER, extprop_video_layout INTEGER, '
       u'extprop_video_chat_height INTEGER, extprop_chat_avatar INTEGER, '
       u'extprop_consumption_timestamp INTEGER, extprop_form_visible '
       u'INTEGER, extprop_recovery_mode INTEGER)',
       u'DbMeta':
       u'CREATE TABLE DbMeta (key TEXT NOT NULL PRIMARY KEY, value TEXT)',
       u'LegacyMessages':
       u'CREATE TABLE LegacyMessages (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER)',
       u'Messages':
       u'CREATE TABLE Messages (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, convo_id INTEGER, chatname TEXT, author TEXT, '
       u'from_dispname TEXT, author_was_live INTEGER, guid BLOB, '
       u'dialog_partner TEXT, timestamp INTEGER, type INTEGER, '
       u'sending_status INTEGER, consumption_status INTEGER, edited_by TEXT, '
       u'edited_timestamp INTEGER, param_key INTEGER, param_value INTEGER, '
       u'body_xml TEXT, identities TEXT, reason TEXT, leavereason INTEGER, '
       u'participant_count INTEGER, error_code INTEGER, chatmsg_type '
       u'INTEGER, chatmsg_status INTEGER, body_is_rawxml INTEGER, oldoptions '
       u'INTEGER, newoptions INTEGER, newrole INTEGER, pk_id INTEGER, crc '
       u'INTEGER, remote_id INTEGER, call_guid TEXT, '
       u'extprop_contact_review_date TEXT, extprop_contact_received_stamp '
       u'INTEGER, extprop_contact_reviewed INTEGER)',
       u'Participants':
       u'CREATE TABLE Participants (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, convo_id INTEGER, identity TEXT, rank '
       u'INTEGER, requested_rank INTEGER, text_status INTEGER, voice_status '
       u'INTEGER, video_status INTEGER, live_identity TEXT, '
       u'live_price_for_me TEXT, live_fwd_identities TEXT, '
       u'live_start_timestamp INTEGER, sound_level INTEGER, debuginfo TEXT, '
       u'next_redial_time INTEGER, nrof_redials_left INTEGER, '
       u'last_voice_error TEXT, quality_problems TEXT, live_type INTEGER, '
       u'live_country TEXT, transferred_by TEXT, transferred_to TEXT, adder '
       u'TEXT, last_leavereason INTEGER, is_premium_video_sponsor INTEGER, '
       u'is_multiparty_video_capable INTEGER, live_identity_to_use TEXT, '
       u'livesession_recovery_in_progress INTEGER, '
       u'is_multiparty_video_updatable INTEGER, real_identity TEXT, '
       u'extprop_default_identity INTEGER)',
       u'SMSes':
       u'CREATE TABLE SMSes (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
       u'INTEGER, type INTEGER, outgoing_reply_type INTEGER, status INTEGER, '
       u'failurereason INTEGER, is_failed_unseen INTEGER, timestamp INTEGER, '
       u'price INTEGER, price_precision INTEGER, price_currency TEXT, '
       u'reply_to_number TEXT, target_numbers TEXT, target_statuses BLOB, '
       u'body TEXT, chatmsg_id INTEGER, identity TEXT, notification_id '
       u'INTEGER, event_flags INTEGER, reply_id_number TEXT, convo_name '
       u'TEXT, extprop_hide_from_history INTEGER, extprop_extended INTEGER)',
       u'Transfers':
       u'CREATE TABLE Transfers (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, type INTEGER, partner_handle TEXT, '
       u'partner_dispname TEXT, status INTEGER, failurereason INTEGER, '
       u'starttime INTEGER, finishtime INTEGER, filepath TEXT, filename '
       u'TEXT, filesize TEXT, bytestransferred TEXT, bytespersecond INTEGER, '
       u'chatmsg_guid BLOB, chatmsg_index INTEGER, convo_id INTEGER, pk_id '
       u'INTEGER, nodeid BLOB, last_activity INTEGER, flags INTEGER, '
       u'old_status INTEGER, old_filepath INTEGER, accepttime INTEGER, '
       u'parent_id INTEGER, offer_send_list TEXT, extprop_localfilename '
       u'TEXT, extprop_hide_from_history INTEGER, extprop_window_visible '
       u'INTEGER, extprop_handled_by_chat INTEGER)',
       u'VideoMessages':
       u'CREATE TABLE VideoMessages (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, qik_id BLOB, attached_msg_ids TEXT, '
       u'sharing_id TEXT, status INTEGER, vod_status INTEGER, vod_path TEXT, '
       u'local_path TEXT, public_link TEXT, progress INTEGER, title TEXT, '
       u'description TEXT, author TEXT, creation_timestamp INTEGER)',
       u'Videos':
       u'CREATE TABLE Videos (id INTEGER NOT NULL PRIMARY KEY, is_permanent '
       u'INTEGER, status INTEGER, error TEXT, debuginfo TEXT, dimensions '
       u'TEXT, media_type INTEGER, duration_1080 INTEGER, duration_720 '
       u'INTEGER, duration_hqv INTEGER, duration_vgad2 INTEGER, '
       u'duration_ltvgad2 INTEGER, timestamp INTEGER, hq_present INTEGER, '
       u'duration_ss INTEGER, ss_timestamp INTEGER, convo_id INTEGER, '
       u'device_path TEXT)',
       u'Voicemails':
       u'CREATE TABLE Voicemails (id INTEGER NOT NULL PRIMARY KEY, '
       u'is_permanent INTEGER, type INTEGER, partner_handle TEXT, '
       u'partner_dispname TEXT, status INTEGER, failurereason INTEGER, '
       u'subject TEXT, timestamp INTEGER, duration INTEGER, allowed_duration '
       u'INTEGER, playback_progress INTEGER, convo_id INTEGER, chatmsg_guid '
       u'BLOB, notification_id INTEGER, flags INTEGER, size INTEGER, path '
       u'TEXT, failures INTEGER, vflags INTEGER, xmsg TEXT, '
       u'extprop_hide_from_history INTEGER)'}]

  def ParseAccountInformation(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses the Accounts database.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    if row['profile_timestamp']:
      event_object = SkypeAccountEvent(
          row['profile_timestamp'], u'Profile Changed', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['authreq_timestamp']:
      event_object = SkypeAccountEvent(
          row['authreq_timestamp'], u'Authenticate Request', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastonline_timestamp']:
      event_object = SkypeAccountEvent(
          row['lastonline_timestamp'], u'Last Online', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['mood_timestamp']:
      event_object = SkypeAccountEvent(
          row['mood_timestamp'], u'Mood Event', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['sent_authrequest_time']:
      event_object = SkypeAccountEvent(
          row['sent_authrequest_time'], u'Auth Request Sent', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

    if row['lastused_timestamp']:
      event_object = SkypeAccountEvent(
          row['lastused_timestamp'], u'Last Used', row['id'],
          row['fullname'], row['given_displayname'], row['emails'],
          row['country'])
      parser_mediator.ProduceEvent(event_object, query=query)

  def ParseChat(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a chat message row.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    to_account = u''
    accounts = []
    participants = row['participants'].split(' ')
    for participant in participants:
      if participant != row['author']:
        accounts.append(participant)
    to_account = u', '.join(accounts)

    if not to_account:
      if row['dialog_partner']:
        to_account = row['dialog_partner']
      else:
        to_account = u'Unknown User'

    event_object = SkypeChatEvent(
        row['timestamp'], row['from_displayname'], row['author'], to_account,
        row['title'], row['body_xml'])
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseSMS(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parse SMS.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    phone_number = row['dstnum_sms']
    if phone_number:
      phone_number = phone_number.replace(u' ', u'')

    event_object = SkypeSMSEvent(row['time_sms'], phone_number, row['msg_sms'])
    parser_mediator.ProduceEvent(event_object, query=query)

  def ParseCall(self, parser_mediator, row, query=None, **unused_kwargs):
    """Parse the calls taking into accounts some rows.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    try:
      aux = row['guid']
      if aux:
        aux_list = aux.split(u'-')
        src_aux = aux_list[0]
        dst_aux = aux_list[1]
      else:
        src_aux = u'Unknown [no GUID]'
        dst_aux = u'Unknown [no GUID]'
    except IndexError:
      src_aux = u'Unknown [{0:s}]'.format(row['guid'])
      dst_aux = u'Unknown [{0:s}]'.format(row['guid'])

    if row['is_incoming'] == u'0':
      user_start_call = True
      source = src_aux
      if row['ip_address']:
        destination = u'{0:s} <{1:s}>'.format(dst_aux, row['ip_address'])
      else:
        destination = dst_aux
    else:
      user_start_call = False
      source = src_aux
      destination = dst_aux

    if row['videostatus'] == u'3':
      video_conference = True
    else:
      video_conference = False

    event_object = SkypeCallEvent(
        row['try_call'], u'WAITING', user_start_call, source, destination,
        video_conference)
    parser_mediator.ProduceEvent(event_object, query=query)

    if row['accept_call']:
      event_object = SkypeCallEvent(
          row['accept_call'], u'ACCEPTED', user_start_call, source,
          destination, video_conference)
      parser_mediator.ProduceEvent(event_object, query=query)

      if row['call_duration']:
        try:
          timestamp = int(row['accept_call']) + int(row['call_duration'])
          event_object = SkypeCallEvent(
              timestamp, u'FINISHED', user_start_call, source, destination,
              video_conference)
          parser_mediator.ProduceEvent(event_object, query=query)

        except ValueError:
          logging.debug((
              u'[{0:s}] Unable to determine when the call {1:s} was '
              u'finished.').format(self.NAME, row['id']))

  def ParseFileTransfer(
      self, parser_mediator, row, cache=None, database=None, query=None,
      **unused_kwargs):
    """Parse the transfer files.

     There is no direct relationship between who sends the file and
     who accepts the file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (sqlite3.Row): row resulting from the query.
      query (Optional[str]): query string.
      cache (Optional[SQLiteCache]): cache object.
      database (Optional[SQLiteDatabase]): database object.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".

    source_dict = cache.GetResults(u'source')
    if not source_dict:
      results = database.Query(self.QUERY_SOURCE_FROM_TRANSFER)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          results, 'source', 'pk_id', ('skypeid', 'skypename'))
      source_dict = cache.GetResults(u'source')

    dest_dict = cache.GetResults(u'destination')
    if not dest_dict:
      results = database.Query(self.QUERY_DEST_FROM_TRANSFER)

      # Note that pysqlite does not accept a Unicode string in row['string'] and
      # will raise "IndexError: Index must be int or string".
      cache.CacheQueryResults(
          results, 'destination', 'parent_id', ('skypeid', 'skypename'))
      dest_dict = cache.GetResults(u'destination')

    source = u'Unknown'
    destination = u'Unknown'

    if row['parent_id']:
      destination = u'{0:s} <{1:s}>'.format(
          row['partner_handle'], row['partner_dispname'])
      skype_id, skype_name = source_dict.get(row['parent_id'], [None, None])
      if skype_name:
        source = u'{0:s} <{1:s}>'.format(skype_id, skype_name)
    else:
      source = u'{0:s} <{1:s}>'.format(
          row['partner_handle'], row['partner_dispname'])

      if row['pk_id']:
        skype_id, skype_name = dest_dict.get(row['pk_id'], [None, None])
        if skype_name:
          destination = u'{0:s} <{1:s}>'.format(skype_id, skype_name)

    try:
      # TODO: add a conversion base.
      file_size = int(row['filesize'])
    except ValueError:
      parser_mediator.ProduceExtractionError(
          u'unable to convert file size: {0!s} of file: {1:s}'.format(
              row['filesize'], row['filename']))
      file_size = 0

    if row['status'] == 8:
      if row['starttime']:
        event_object = SkypeTransferFileEvent(
            row['starttime'], row['id'], u'GETSOLICITUDE', source, destination,
            row['filename'], row['filepath'], file_size)
        parser_mediator.ProduceEvent(event_object, query=query)

      if row['accepttime']:
        event_object = SkypeTransferFileEvent(
            row['accepttime'], row['id'], u'ACCEPTED', source, destination,
            row['filename'], row['filepath'], file_size)
        parser_mediator.ProduceEvent(event_object, query=query)

      if row['finishtime']:
        event_object = SkypeTransferFileEvent(
            row['finishtime'], row['id'], u'FINISHED', source, destination,
            row['filename'], row['filepath'], file_size)
        parser_mediator.ProduceEvent(event_object, query=query)

    elif row['status'] == 2 and row['starttime']:
      event_object = SkypeTransferFileEvent(
          row['starttime'], row['id'], u'SENDSOLICITUDE', source, destination,
          row['filename'], row['filepath'], file_size)
      parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(SkypePlugin)
