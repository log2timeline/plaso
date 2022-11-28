# -*- coding:utf-8 -*-
"""SQLite parser plugin for Twitter on Android database files."""

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class AndroidTwitterContactEventData(events.EventData):
  """Twitter on Android contact event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the contact was
        created.
    description (str): twitter account profile description.
    followers (int): number of followers.
    friends (int): number of following.
    friendship_time (dfdatetime.DateTimeValues): date and time the contact was
        befriended.
    identifier (int): contact row id.
    image_url (str): profile picture url.
    location (str): twitter account profile location content.
    modification_time (dfdatetime.DateTimeValues): date and time the contact was
        last modified.
    name (str): twitter account name.
    query (str): SQL query that was used to obtain the event data.
    statuses (int): twitter account number of tweets.
    user_identifier (int): twitter account id.
    username (str): twitter account handler.
    web_url (str): twitter account profile url content.
  """

  DATA_TYPE = 'android:twitter:contact'

  def __init__(self):
    """Initializes event data."""
    super(AndroidTwitterContactEventData,
          self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.description = None
    self.followers = None
    self.friendship_time = None
    self.friends = None
    self.identifier = None
    self.image_url = None
    self.location = None
    self.modification_time = None
    self.name = None
    self.query = None
    self.statuses = None
    self.user_identifier = None
    self.username = None
    self.web_url = None


class AndroidTwitterSearchEventData(events.EventData):
  """Twitter on Android search event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the search was
        created.
    name (str): twitter name handler.
    query (str): SQL query that was used to obtain the event data.
    search_query (str): search query.
  """

  DATA_TYPE = 'android:twitter:search'

  def __init__(self):
    """Initializes event data."""
    super(AndroidTwitterSearchEventData,self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.name = None
    self.query = None
    self.search_query = None


class AndroidTwitterStatusEventData(events.EventData):
  """Twitter on Android status event data.

  Attributes:
    author_identifier (int): twitter account identifier.
    content (str): status content.
    creation_time (dfdatetime.DateTimeValues): date and time the status was
        created.
    favorited (int): favorited flag as 0/1 value.
    identifier (int): status row identifier.
    query (str): SQL query that was used to obtain the event data.
    retweeted (int): retweeted flag as 0/1 value.
    username (str): twitter account handler.
  """

  DATA_TYPE = 'android:twitter:status'

  def __init__(self):
    """Initializes event data."""
    super(AndroidTwitterStatusEventData,self).__init__(data_type=self.DATA_TYPE)
    self.author_identifier = None
    self.content = None
    self.creation_time = None
    self.favorited = None
    self.identifier = None
    self.query = None
    self.retweeted = None
    self.username = None


class AndroidTwitterPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Twitter on Android database files."""

  NAME = 'twitter_android'
  DATA_FORMAT = 'Twitter on Android SQLite database file'

  REQUIRED_STRUCTURE = {
      'search_queries': frozenset([
          'name', 'query', 'time']),
      'statuses': frozenset([
          '_id', 'author_id', 'content', 'created', 'favorited', 'retweeted']),
      'users': frozenset([
          'username', 'user_id', '_id', 'name', 'profile_created',
          'description', 'web_url', 'location', 'followers', 'friends',
          'statuses', 'image_url', 'updated', 'friendship_time'])}

  QUERIES = [
      ('SELECT name, query, time FROM search_queries', 'ParseSearchRow'),
      (('SELECT statuses._id AS _id, statuses.author_id AS author_id, '
        'users.username AS username, statuses.content AS content, '
        'statuses.created AS time, statuses.favorited AS favorited, '
        'statuses.retweeted AS retweeted FROM statuses LEFT JOIN users ON '
        'statuses.author_id = users.user_id'), 'ParseStatusRow'),
      (('SELECT _id, user_id, username, name, profile_created, description, '
        'web_url, location, followers, friends, statuses, image_url, updated, '
        'friendship_time FROM users'), 'ParseContactRow')]

  SCHEMAS = [{
      'activities': (
          'CREATE TABLE activities (_id INTEGER PRIMARY KEY,type INT,event '
          'INT,created_at INT,hash INT,max_position INT,min_position '
          'INT,sources_size INT,source_type INT,sources BLOB,targets_size '
          'INT,target_type INT,targets BLOB,target_objects_size '
          'INT,target_object_type INT,target_objects BLOB,is_last INT,tag '
          'INT,magic_rec_id INT,UNIQUE (type, max_position) ON CONFLICT '
          'REPLACE)'),
      'ads_account_permissions': (
          'CREATE TABLE ads_account_permissions (_id INTEGER PRIMARY '
          'KEY,promotable_users BLOB,last_synced INT NOT NULL)'),
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'business_profiles': (
          'CREATE TABLE business_profiles (_id INTEGER PRIMARY KEY,user_id '
          'INT UNIQUE NOT NULL,business_profile BLOB,last_synced INT NOT '
          'NULL)'),
      'card_state': (
          'CREATE TABLE card_state (_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,card_status_id INT,card_id INT, card_state BLOB)'),
      'category_timestamp': (
          'CREATE TABLE category_timestamp (_id INTEGER PRIMARY '
          'KEY,cat_status_id INT NOT NULL,cat_tag INT NOT NULL,cat_timestamp '
          'INT NOT NULL)'),
      'clusters': (
          'CREATE TABLE clusters (_id INTEGER PRIMARY KEY,cl_cluster_id TEXT '
          'UNIQUE NOT NULL,cl_type INT,cl_title TEXT,cl_subtitle TEXT,cl_size '
          'INT,cl_timestamp INT,cl_content BLOB)'),
      'conversation_entries': (
          'CREATE TABLE conversation_entries (_id INTEGER PRIMARY '
          'KEY,entry_id INT UNIQUE NOT NULL,sort_entry_id INT UNIQUE NOT '
          'NULL,conversation_id TEXT,user_id INT,created INT,entry_type '
          'INT,data BLOB,request_id TEXT)'),
      'conversation_participants': (
          'CREATE TABLE conversation_participants (_id INTEGER PRIMARY '
          'KEY,conversation_id TEXT NOT NULL,user_id TEXT NOT NULL,join_time '
          'INT NOT NULL,participant_type INT NOT NULL)'),
      'conversations': (
          'CREATE TABLE conversations (_id INTEGER PRIMARY '
          'KEY,conversation_id TEXT UNIQUE NOT NULL,title TEXT,avatar_url '
          'TEXT,type INT,sort_event_id BIGINT,last_readable_event_id '
          'BIGINT,last_read_event_id BIGINT,sort_timestamp BIGINT,is_muted '
          'INT,min_event_id BIGINT,is_hidden INT,has_more INT,read_only INT)'),
      'cursors': (
          'CREATE TABLE cursors (_id INTEGER PRIMARY KEY,kind INT,type '
          'INT,owner_id INT,ref_id TEXT,next TEXT)'),
      'dismiss_info': (
          'CREATE TABLE dismiss_info(timeline_id INTEGER REFERENCES '
          'timeline(_id),feedback_action_id INTEGER REFERENCES '
          'feedback_action(_id),UNIQUE(timeline_id,feedback_action_id))'),
      'feedback_action': (
          'CREATE TABLE feedback_action(_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,feedback_type TEXT,prompt TEXT,confirmation '
          'TEXT,UNIQUE(feedback_type,prompt,confirmation))'),
      'list_mapping': (
          'CREATE TABLE list_mapping (_id INTEGER PRIMARY '
          'KEY,list_mapping_list_id TEXT,list_mapping_type '
          'INT,list_mapping_user_id INT,list_is_last INT)'),
      'locations': (
          'CREATE TABLE locations (_id INTEGER PRIMARY KEY,name TEXT,woeid '
          'INT,country TEXT,country_code TEXT)'),
      'moments': (
          'CREATE TABLE moments (_id INTEGER PRIMARY KEY,title TEXT NOT '
          'NULL,can_subscribe INT,is_live INT,is_sensitive '
          'INT,subcategory_string TEXT,subcategory_favicon_url '
          'TEXT,time_string TEXT,duration_string TEXT,is_subscribed '
          'INT,description TEXT NOT NULL,moment_url TEXT,num_subscribers '
          'INT,author_info BLOB,promoted_content BLOB)'),
      'moments_guide': (
          'CREATE TABLE moments_guide (_id INTEGER PRIMARY KEY,moment_id INT '
          'NOT NULL,section_id INT NOT NULL,tweet_id INT NOT NULL, crop_data '
          'BLOB,media_id INT,media_url TEXT,media_size BLOB,FOREIGN '
          'KEY(section_id) REFERENCES moments_sections(_id) ON DELETE '
          'CASCADE)'),
      'moments_guide_categories': (
          'CREATE TABLE moments_guide_categories (_id INTEGER PRIMARY '
          'KEY,category_id TEXT NOT NULL,is_default_category INT NOT '
          'NULL,category_name TEXT NOT NULL,fetch_timestamp INT NOT NULL)'),
      'moments_guide_user_states': (
          'CREATE TABLE moments_guide_user_states (_id INTEGER PRIMARY '
          'KEY,moment_id INT NOT NULL,is_read INT,is_updated INT,FOREIGN '
          'KEY(moment_id) REFERENCES moments(_id) ON DELETE CASCADE)'),
      'moments_pages': (
          'CREATE TABLE moments_pages (_id INTEGER PRIMARY KEY,moment_id INT '
          'NOT NULL,page_id TEXT,type BLOB,tweet_id INT,display_mode '
          'BLOB,page_number INT,crop_data BLOB,theme_data BLOB,media_id '
          'INT,media_size BLOB,media_url TEXT,last_read_timestamp INT,FOREIGN '
          'KEY(moment_id) REFERENCES moments(_id))'),
      'moments_sections': (
          'CREATE TABLE moments_sections (_id INTEGER PRIMARY '
          'KEY,section_title TEXT,section_type BLOB NOT NULL,section_group_id '
          'TEXT,section_group_type INT NOT NULL)'),
      'moments_visit_badge': (
          'CREATE TABLE moments_visit_badge (_id INTEGER PRIMARY '
          'KEY,moment_id INT UNIQUE NOT NULL,is_new_since_visit '
          'INT,is_updated_since_visit INT)'),
      'news': (
          'CREATE TABLE news (_id INTEGER PRIMARY KEY AUTOINCREMENT,country '
          'TEXT,language TEXT,topic_id INT,news_id TEXT,title TEXT,image_url '
          'TEXT,author_name TEXT,article_description TEXT,article_url '
          'TEXT,tweet_count INT,start_time INT,news_id_hash INT)'),
      'notifications': (
          'CREATE TABLE notifications (_id INTEGER PRIMARY KEY,type '
          'INT,notif_id INT,source_user_name TEXT,s_name TEXT,s_id '
          'INT,notif_txt TEXT,aggregation_data TEXT,notif_extra_data BLOB)'),
      'one_click': (
          'CREATE TABLE one_click (_id INTEGER PRIMARY KEY,topic '
          'TEXT,filter_name TEXT,filter_location TEXT,filter_follow INT)'),
      'order_history': (
          'CREATE TABLE order_history (_id INTEGER PRIMARY KEY,ordered_at INT '
          ',order_id INT ,data BLOB)'),
      'promoted_retry': (
          'CREATE TABLE promoted_retry(impression_id TEXT,event INT NOT '
          'NULL,is_earned INT NOT NULL,trend_id INT,num_retries INT NOT '
          'NULL,url TEXT,video_playlist_url TEXT,video_content_uuid '
          'TEXT,video_content_type TEXT,video_cta_url TEXT,video_cta_app_id '
          'TEXT,video_cta_app_name TEXT,card_event TEXT,PRIMARY '
          'KEY(impression_id,event,is_earned,trend_id))'),
      'prompts': (
          'CREATE TABLE prompts (_id INTEGER PRIMARY KEY,p_id INT,p_format '
          'TEXT,p_template TEXT,p_header TEXT,p_text TEXT,p_action_text '
          'TEXT,p_action_url TEXT,p_icon TEXT,p_background_image_url '
          'TEXT,p_persistence TEXT,p_entities BLOB,p_header_entities '
          'BLOB,p_status_id LONG,p_insertion_index INT,p_trigger TEXT)'),
      'rankings': (
          'CREATE TABLE rankings (_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,country TEXT,language TEXT,granularity TEXT,category '
          'TEXT,date INT)'),
      'search_queries': (
          'CREATE TABLE search_queries (_id INTEGER PRIMARY KEY,type INT,name '
          'TEXT NOT NULL,query TEXT NOT NULL,query_id INT,time INT,latitude '
          'REAL,longitude REAL,radius REAL,location TEXT,pc '
          'BLOB,cluster_titles BLOB)'),
      'search_results': (
          'CREATE TABLE search_results (_id INTEGER PRIMARY KEY,search_id '
          'INT,s_type INT,data_type INT,type_id INT,polled INT,data_id '
          'INT,related_data BLOB,cluster_id INT)'),
      'search_suggestion_metadata': (
          'CREATE TABLE search_suggestion_metadata (_id INTEGER PRIMARY '
          'KEY,type INT,last_update LONG)'),
      'status_groups': (
          'CREATE TABLE status_groups (_id INTEGER PRIMARY KEY,tweet_type INT '
          'DEFAULT 0,type INT,sender_id INT,owner_id INT,ref_id INT,tag '
          'INT,g_status_id INT,is_read INT,page INT,is_last INT,updated_at '
          'INT,timeline INT,pc BLOB,g_flags INT,preview_draft_id '
          'INT,preview_media BLOB,tweet_pivots BLOB)'),
      'status_metadata': (
          'CREATE TABLE status_metadata (_id INTEGER PRIMARY KEY,owner_id INT '
          'NOT NULL,status_id INT NOT NULL,status_group INT NOT '
          'NULL,status_group_tag INT NOT NULL,soc_type INT,soc_name '
          'TEXT,soc_second_name TEXT,soc_others_count INT,soc_fav_count '
          'INT,soc_rt_count INT,reason_icon_type TEXT,reason_text '
          'TEXT,scribe_component TEXT,scribe_data BLOB,highlights TEXT)'),
      'statuses': (
          'CREATE TABLE statuses (_id INTEGER PRIMARY KEY,status_id INT '
          'UNIQUE NOT NULL,author_id INT,content TEXT,source TEXT,created '
          'INT,in_r_user_id INT,in_r_status_id INT,favorited INT,latitude '
          'TEXT,longitude TEXT,place_data BLOB,entities TEXT,retweet_count '
          'INT,r_content TEXT,cards BLOB,flags INT,favorite_count INT,lang '
          'TEXT,supplemental_language TEXT,view_count INT,quoted_tweet_data '
          'BLOB,quoted_tweet_id INT,retweeted INT)'),
      'stories': (
          'CREATE TABLE stories ( _id INTEGER PRIMARY KEY,story_id '
          'TEXT,story_order INT,story_type INT,story_proof_type '
          'INT,story_proof_addl_count INT,data_type INT,data_id '
          'INT,story_is_read INT,story_meta_title TEXT,story_meta_subtitle '
          'TEXT,story_meta_query TEXT,story_meta_header_img_url '
          'TEXT,story_source TEXT,story_impression_info TEXT,story_tag INT)'),
      'timeline': (
          'CREATE TABLE timeline (_id INTEGER PRIMARY KEY '
          'AUTOINCREMENT,owner_id INT,type INT,sort_index INT,entity_id '
          'INT,entity_type INT,data_type INT,data_type_group '
          'INT,data_type_tag INT,timeline_tag TEXT,timeline_group_id '
          'INT,timeline_scribe_group_id INT,data_id INT,data BLOB,flags '
          'INT,updated_at INT,data_origin_id TEXT,is_last INT,is_read '
          'INT,scribe_content BLOB,timeline_moment_info BLOB,dismissed INT '
          'NOT NULL DEFAULT 0,dismiss_actions INT NOT NULL DEFAULT 0)'),
      'tokens': (
          'CREATE TABLE tokens (_id INTEGER PRIMARY KEY,text TEXT,weight '
          'INT,type INT,ref_id INT)'),
      'topics': (
          'CREATE TABLE topics (_id INTEGER PRIMARY KEY,ev_id TEXT UNIQUE NOT '
          'NULL,ev_type INT,ev_query TEXT NOT NULL,ev_seed_hashtag '
          'TEXT,ev_title STRING,ev_subtitle STRING,ev_view_url '
          'STRING,ev_status STRING,ev_image_url TEXT,ev_explanation '
          'TEXT,ev_tweet_count INT,ev_start_time INT,ev_owner_id INT,ev_pc '
          'BLOB,ev_content BLOB,ev_hash INT)'),
      'user_groups': (
          'CREATE TABLE user_groups (_id INTEGER PRIMARY KEY,type INT,tag '
          'INT,rank INT,owner_id INT,user_id INT,is_last INT,pc BLOB,g_flags '
          'INT)'),
      'user_metadata': (
          'CREATE TABLE user_metadata (_id INTEGER PRIMARY KEY,owner_id INT '
          'NOT NULL,user_id INT NOT NULL,user_group_type INT NOT '
          'NULL,user_group_tag INT NOT NULL,soc_type INT,soc_name '
          'TEXT,soc_follow_count INT,user_title TEXT,token TEXT)'),
      'users': (
          'CREATE TABLE users (_id INTEGER PRIMARY KEY,user_id INT UNIQUE NOT '
          'NULL,username TEXT,name TEXT,description TEXT,web_url '
          'TEXT,bg_color INT,location TEXT,structured_location '
          'BLOB,user_flags INT,followers INT,fast_followers INT DEFAULT '
          '0,friends INT,statuses INT,profile_created INT,image_url TEXT,hash '
          'INT,updated INT,friendship INT,friendship_time INT,favorites INT '
          'DEFAULT 0,header_url TEXT,description_entities BLOB,url_entities '
          'BLOB,media_count INT,extended_profile_fields BLOB,pinned_tweet_id '
          'INT,link_color INT,advertiser_type TEXT,business_profile_state '
          'TEXT)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.JavaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_java_time.JavaTime(timestamp=timestamp)

  def ParseSearchRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a search row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = AndroidTwitterSearchEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'time')
    event_data.query = query
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.search_query = self._GetRowValue(query_hash, row, 'query')

    parser_mediator.ProduceEventData(event_data)

  def ParseStatusRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a status row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = AndroidTwitterStatusEventData()
    event_data.author_identifier = self._GetRowValue(
        query_hash, row, 'author_id')
    event_data.content = self._GetRowValue(query_hash, row, 'content')
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'time')
    event_data.favorited = self._GetRowValue(query_hash, row, 'favorited')
    event_data.identifier = self._GetRowValue(query_hash, row, '_id')
    event_data.query = query
    event_data.retweeted = self._GetRowValue(query_hash, row, 'retweeted')
    event_data.username = self._GetRowValue(query_hash, row, 'username')

    parser_mediator.ProduceEventData(event_data)

  def ParseContactRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a status row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    query_hash = hash(query)

    event_data = AndroidTwitterContactEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'profile_created')
    event_data.description = self._GetRowValue(query_hash, row, 'description')
    event_data.followers = self._GetRowValue(query_hash, row, 'followers')
    event_data.friends = self._GetRowValue(query_hash, row, 'friends')
    event_data.friendship_time = self._GetDateTimeRowValue(
        query_hash, row, 'friendship_time')
    event_data.identifier = self._GetRowValue(query_hash, row, '_id')
    event_data.image_url = self._GetRowValue(query_hash, row, 'image_url')
    event_data.location = self._GetRowValue(query_hash, row, 'location')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'updated')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.query = query
    event_data.statuses = self._GetRowValue(query_hash, row, 'statuses')
    event_data.user_identifier = self._GetRowValue(query_hash, row, 'user_id')
    event_data.username = self._GetRowValue(query_hash, row, 'username')
    event_data.web_url = self._GetRowValue(query_hash, row, 'web_url')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(AndroidTwitterPlugin)
